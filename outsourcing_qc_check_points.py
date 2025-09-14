import pandas as pd
from datetime import datetime
from pathlib import Path
from checkpoint_strategies import CheckpointRegistry, PackageReadinessCheckpoint, FinalReportCheckpoint

class OutsourcingQcCheckPoints:
    def __init__(self, df):
        self.df = df
        self.today = datetime.now()
        
        # Initialize the checkpoint registry with default checkpoints
        CheckpointRegistry.clear()
        CheckpointRegistry.register(PackageReadinessCheckpoint())
        CheckpointRegistry.register(FinalReportCheckpoint())

    def get_failures(self):
        """
        Returns a dictionary of all failed rules.
        Now uses the extensible checkpoint system internally.
        """
        failures = {}
        
        for checkpoint in CheckpointRegistry.get_all_checkpoints():
            failures[checkpoint.name] = []
            
            for index, row in self.df.iterrows():
                if checkpoint.should_check(row, self.today):
                    checkpoint_failures = checkpoint.execute_check(row, self.today)
                    failures[checkpoint.name].extend(checkpoint_failures)
        
        return failures

    def add_checkpoint(self, checkpoint):
        """Add a new checkpoint to the registry."""
        CheckpointRegistry.register(checkpoint)
    
    def remove_checkpoint(self, checkpoint_name: str):
        """Remove a checkpoint by name from the registry."""
        CheckpointRegistry.unregister(checkpoint_name)
    
    def list_checkpoints(self):
        """List all registered checkpoint names."""
        return [cp.name for cp in CheckpointRegistry.get_all_checkpoints()]