import os
import pandas as pd
from datetime import datetime
from src.utils.load_config import LoadConfig
from asyncio import Lock, get_running_loop


app_config = LoadConfig()
class Logger:
    def __init__(self):
        # Initialize an empty DataFrame with specified columns
        self.log_df = pd.DataFrame(columns=['Date', 'Time', 'User', 'Query', 'Response', 'Rating', 'Comments'])
        # Initialize a temporary storage for the current log entry
        self.current_entry = {key: None for key in self.log_df.columns}
        self.log_file_dir = app_config.log_file
        self.lock = Lock()

    async def _update_current_entry(self, key, value):
        """Helper function to update the current log entry"""
        if key in self.current_entry:
            self.current_entry[key] = value
        else:
            raise ValueError(f"Invalid key: {key}")

    async def set_date_time(self, date, time):
        await self._update_current_entry('Date', date)
        await self._update_current_entry('Time', time)

    async def set_user(self, user):
        await self._update_current_entry('User', user)

    async def set_query(self, query):
        await self._update_current_entry('Query', query)

    async def set_response(self, response):
        await self._update_current_entry('Response', response)

    async def set_rating(self, rating):
        await self._update_current_entry('Rating', rating)

    async def set_comments(self, comments):
        await self._update_current_entry('Comments', comments)

    async def commit_log_entry(self):
        """Finalize and log the current entry, then reset for the next entry"""
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        await self.set_date_time(date, time)
        await self._save_log_to_csv()


    async def print_df(self):
        """Print the entire log DataFrame"""
        print(self.current_entry)

    async def _save_log_to_csv(self):
        """Asynchronously save the log DataFrame to a CSV file, appending if the file already exists, in a thread-safe manner."""
        async with self.lock:
            """Save the log DataFrame to a CSV file, appending if the file already exists."""
            # Check if the file exists to determine if we need to write headers
            file_exists = os.path.isfile(app_config.log_file)

            entry_df = pd.DataFrame([self.current_entry])
            self.log_df = pd.concat([self.log_df, entry_df], ignore_index=True)

            loop = get_running_loop()
            await loop.run_in_executor(
                None,  # Executor, None uses the default executor (ThreadPoolExecutor)
                lambda: self.log_df.to_csv(app_config.log_file, mode='a', index=False, header=not file_exists)
            )

            # Clear the DataFrame after saving to avoid appending the same logs again on subsequent saves
            self.log_df = self.log_df.iloc[0:0]
