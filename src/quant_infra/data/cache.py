"""Data caching utilities."""

from datetime import datetime
from typing import Optional
from pathlib import Path
import pickle
import json
from functools import wraps

import polars as pl


class DataCache:
    """Local data cache with LRU eviction."""
    
    def __init__(self, cache_dir: str = "~/.quant-cache", max_size_gb: float = 10.0):
        """
        Initialize cache.
        
        Args:
            cache_dir: Cache directory
            max_size_gb: Max cache size in GB
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_gb * 1024**3
        self.metadata_file = self.cache_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load cache metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"entries": {}, "total_size": 0}
    
    def _save_metadata(self) -> None:
        """Save cache metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _evict_if_needed(self, new_size: int) -> None:
        """Evict oldest entries if needed."""
        while self.metadata["total_size"] + new_size > self.max_size_bytes and self.metadata["entries"]:
            # Find oldest entry
            oldest_key = min(
                self.metadata["entries"].keys(),
                key=lambda k: self.metadata["entries"][k]["timestamp"]
            )
            self._delete_entry(oldest_key)
    
    def _delete_entry(self, key: str) -> None:
        """Delete a cache entry."""
        path = self.cache_dir / f"{key}.pkl"
        if path.exists():
            path.unlink()
        self.metadata["total_size"] -= self.metadata["entries"][key]["size"]
        del self.metadata["entries"][key]
        self._save_metadata()
    
    def _get_key(self, symbol: str, interval: str, start: datetime, end: datetime) -> str:
        """Generate cache key."""
        return f"{symbol}_{interval}_{start.isoformat()}_{end.isoformat()}"
    
    def get(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime
    ) -> Optional[pl.DataFrame]:
        """Get data from cache."""
        key = self._get_key(symbol, interval, start, end)
        
        if key in self.metadata["entries"]:
            path = self.cache_dir / f"{key}.pkl"
            if path.exists():
                with open(path, 'rb') as f:
                    df = pickle.load(f)
                self.metadata["entries"][key]["timestamp"] = datetime.now().timestamp()
                self._save_metadata()
                return df
        
        return None
    
    def set(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        df: pl.DataFrame
    ) -> None:
        """Set data in cache."""
        key = self._get_key(symbol, interval, start, end)
        
        # Calculate size
        size = df.estimated_size()
        
        # Evict if needed
        self._evict_if_needed(size)
        
        # Save data
        path = self.cache_dir / f"{key}.pkl"
        with open(path, 'wb') as f:
            pickle.dump(df, f)
        
        # Update metadata
        self.metadata["entries"][key] = {
            "timestamp": datetime.now().timestamp(),
            "size": size,
            "symbol": symbol,
            "interval": interval,
        }
        self.metadata["total_size"] += size
        self._save_metadata()
    
    def clear(self) -> None:
        """Clear all cache."""
        for key in list(self.metadata["entries"].keys()):
            self._delete_entry(key)
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "total_size_gb": self.metadata["total_size"] / 1024**3,
            "num_entries": len(self.metadata["entries"]),
            "max_size_gb": self.max_size_bytes / 1024**3,
        }


def cached(cache: DataCache):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract params from args/kwargs
            symbol = kwargs.get('symbol', args[0] if args else None)
            interval = kwargs.get('interval', '1h')
            start = kwargs.get('start', args[1] if len(args) > 1 else None)
            end = kwargs.get('end', args[2] if len(args) > 2 else None)
            
            if symbol and start and end:
                cached_df = cache.get(symbol, interval, start, end)
                if cached_df is not None:
                    return cached_df
            
            result = func(*args, **kwargs)
            
            if symbol and start and end:
                cache.set(symbol, interval, start, end, result)
            
            return result
        
        return wrapper
    return decorator
