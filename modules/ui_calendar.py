# modules/ui_calendar.py
from calendar import HTMLCalendar
from datetime import date

class FestivalCalendar(HTMLCalendar):
    def __init__(self, festival_dates_map):
        super().__init__()
        self.festival_dates_map = festival_dates_map

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        
        day_str = f"{self.year}-{self.month:02d}-{day:02d}"
        
        if day_str in self.festival_dates_map:
            cssclass = 'festival'
            fest_names = "\n".join(self.festival_dates_map[day_str])
            return f'<td class="{cssclass}" title="{fest_names}">{day}</td>'
        else:
            return f'<td>{day}</td>'

    def formatmonth(self, theyear, themonth, withyear=True):
        self.year, self.month = theyear, themonth
        return super().formatmonth(theyear, themonth, withyear)

def render_month_calendar(year, month, festival_dates_map):
    cal = FestivalCalendar(festival_dates_map)
    html_cal = cal.formatmonth(year, month)
    
    # Custom CSS for highlighting
    st_style = """
        <style>
            .festival { background-color: orange; color: white; border-radius: 50%; }
            table { width: 100%; }
            th, td { text-align: center; padding: 5px; }
        </style>
    """
    return st_style + html_cal