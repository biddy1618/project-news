import datetime
import logging

from typing import List


class Helper():
    
    @staticmethod
    def _message(msg: str, e: Exception = None) -> str:
        """
        Helper function to print messages.

        Args:
            msg (str): message.
            e (Exception, optional): Exception if raised. Defaults to None.

        Returns:
            str: message formatted.
        """
        if e: return f'{msg}. Exception: "{e}".'
        else: return f'{msg}'    
    
    @staticmethod
    def generate_dates(start_date: str, end_date: str = None, logger: logging.Logger = None) -> List[str]:        
        """
        Generates date(s) for fetching url links for specific dates.

        Args:
            startDate (str): start date in format "dd.mm.yyyy".
            endDate (str, optional): end date in format "dd.mm.yyyy", should be later than start date. 
            Defaults to None.

        Returns:
            List[str]: list of dates for the given date range (days).
        """
        format = '%d.%m.%Y'
        try:
            start_date = datetime.datetime.strptime(start_date, format)
            end_date = datetime.datetime.strptime(end_date, format) if end_date is not None else start_date + datetime.timedelta(days=1)
        except ValueError as e:
            logger.error(Helper._message('Invalid date format: {start_date}, {end_date}. Input the date in following format: "dd.mm.yyyy"', e))
            raise SystemExit(e)
        
        if start_date >= end_date:
            logger.error(Helper._message('Make sure that the end date is after the start date'))
            raise SystemExit()
        
        date_generated = [(start_date + datetime.timedelta(days=x)).strftime(format) for x in range(0, (end_date-start_date).days)]

        return date_generated
