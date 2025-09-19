# modules/ics_calendar_integration.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
import pickle
import json

# ICS parsing imports
try:
    from icalendar import Calendar, Event
except ImportError:
    st.error("Please install icalendar: pip install icalendar")

class ICSCalendarIntegration:
    def __init__(self):
        self.festivals_cache = {}
        self.local_ics_file = 'data/indian_festivals.ics'
        self.festivals_json_file = 'data/festivals_database.json'
        self.cache_metadata_file = 'data/festivals_cache_metadata.json'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
    def initialize_festival_database(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Initialize festival database from local files or fetch from Google Calendar.
        This covers 50+ years of past and future festivals.
        """
        # Check if we need to refresh the database
        if force_refresh or self._should_refresh_database():
            st.info("Initializing comprehensive festival database (50+ years coverage)...")
            return self._fetch_and_store_comprehensive_festivals()
        else:
            # Load from local JSON database
            if os.path.exists(self.festivals_json_file):
                return self._load_local_festival_database()
            else:
                # First time setup
                st.info("Setting up festival database for the first time...")
                return self._fetch_and_store_comprehensive_festivals()
    
    def _should_refresh_database(self) -> bool:
        """Check if database needs refresh (older than 6 months)"""
        if not os.path.exists(self.cache_metadata_file):
            return True
        
        try:
            with open(self.cache_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            last_update = datetime.fromisoformat(metadata.get('last_update', '1900-01-01'))
            age_days = (datetime.now() - last_update).days
            
            return age_days > 180  # Refresh every 6 months
        except:
            return True
    
    def _fetch_and_store_comprehensive_festivals(self) -> Dict[str, Dict]:
        """
        Fetch comprehensive festival data and store locally.
        This attempts to get maximum historical and future coverage.
        """
        all_festivals = {}
        
        # Multiple calendar sources for comprehensive coverage
        calendar_sources = [
            {
                'name': 'Indian National Holidays',
                'id': 'en.indian%23holiday@group.v.calendar.google.com'
            },
            {
                'name': 'Hindu Calendar',
                'id': 'hindu.festivals.calendar%40gmail.com'
            },
            {
                'name': 'Indian Festivals',
                'id': 'indian.festivals%40gmail.com'
            }
        ]
        
        successful_fetches = 0
        
        for source in calendar_sources:
            try:
                st.info(f"Fetching from {source['name']}...")
                festivals = self._fetch_calendar_source(source['id'])
                
                if festivals:
                    # Merge festivals (avoid duplicates by date)
                    for date_str, festival_info in festivals.items():
                        if date_str not in all_festivals:
                            all_festivals[date_str] = festival_info
                        else:
                            # If duplicate date, prefer more detailed entry
                            existing = all_festivals[date_str]
                            if len(festival_info.get('description', '')) > len(existing.get('description', '')):
                                all_festivals[date_str] = festival_info
                    
                    successful_fetches += 1
                    st.success(f"✓ Fetched {len(festivals)} events from {source['name']}")
                else:
                    st.warning(f"✗ No data from {source['name']}")
                    
            except Exception as e:
                st.warning(f"✗ Failed to fetch from {source['name']}: {str(e)}")
        
        if successful_fetches == 0:
            st.error("Failed to fetch from any calendar source. Creating minimal fallback database.")
            all_festivals = self._create_minimal_fallback_database()
        
        # Store the comprehensive database
        self._save_festival_database(all_festivals)
        
        # Also save raw ICS for reference
        if all_festivals:
            self._save_ics_locally(all_festivals)
        
        st.success(f"🎉 Festival database created with {len(all_festivals)} festivals")
        st.info(f"Coverage: {self._get_date_coverage(all_festivals)}")
        
        return all_festivals
    
    def _fetch_calendar_source(self, calendar_id: str) -> Dict[str, Dict]:
        """Fetch festivals from a single calendar source"""
        try:
            ics_url = f'https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics'
            
            response = requests.get(ics_url, timeout=30)
            response.raise_for_status()
            
            return self.parse_ics_content(response.text)
            
        except Exception as e:
            raise Exception(f"Failed to fetch calendar {calendar_id}: {str(e)}")
    
    def parse_ics_content(self, ics_content: str) -> Dict[str, Dict]:
        """Parse ICS content and extract all events as potential festivals"""
        festivals = {}
        
        try:
            cal = Calendar.from_ical(ics_content)
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    summary = str(component.get('summary', ''))
                    dtstart = component.get('dtstart')
                    
                    if dtstart and summary:
                        # Handle different date formats from ICS
                        try:
                            if hasattr(dtstart.dt, 'hour'):
                                event_date = dtstart.dt
                            else:
                                event_date = datetime.combine(dtstart.dt, datetime.min.time())
                        except:
                            continue
                        
                        # Only include events that look like festivals
                        if self._is_likely_festival(summary):
                            date_str = event_date.strftime('%Y-%m-%d')
                            festivals[date_str] = {
                                'name': summary.strip(),
                                'date': event_date,
                                'description': str(component.get('description', '')).strip(),
                                'source': 'ics_import'
                            }
        
        except Exception as e:
            st.warning(f"Error parsing ICS content: {e}")
        
        return festivals
    
    def _is_likely_festival(self, event_name: str) -> bool:
        """Determine if an event is likely a festival"""
        name_lower = event_name.lower().strip()
        
        # Exclude clearly non-festival events
        excluded_keywords = [
            'independence day', 'republic day', 'gandhi jayanti',
            'birthday', 'death anniversary', 'national', 'international',
            'world', 'day of', 'awareness', 'week', 'month', 'memorial',
            'remembrance', 'solidarity', 'earth day', 'environment',
            'health', 'safety', 'awareness', 'conference', 'meeting'
        ]
        
        for excluded in excluded_keywords:
            if excluded in name_lower:
                return False
        
        # Include festival-related keywords
        festival_keywords = [
            'diwali', 'deepavali', 'holi', 'dussehra', 'dasara', 'vijayadashami',
            'ganesh', 'ganapati', 'navratri', 'durga', 'kali', 'lakshmi',
            'karva', 'karwa', 'raksha', 'rakhi', 'janmashtami', 'krishna',
            'ram navami', 'hanuman', 'shivratri', 'makar sankranti', 'pongal',
            'baisakhi', 'vaisakhi', 'onam', 'vishu', 'ugadi', 'gudi padwa',
            'akshaya tritiya', 'teej', 'ahoi ashtami', 'dhanteras', 'govardhan',
            'bhai dooj', 'chhath', 'kartikeya', 'ganga dussehra', 'rath yatra',
            'guru nanak', 'guru gobind', 'vasant panchami', 'magh purnima',
            'maharana pratap', 'chhatrapati', 'festival', 'celebration',
            'eid', 'ramadan', 'muharram', 'christmas', 'good friday', 'easter',
            'pooja', 'puja', 'jayanti', 'vratam', 'vrata', 'chaturthi',
            'purnima', 'amavasya', 'ekadashi', 'sankranti', 'vivah'
        ]
        
        return any(keyword in name_lower for keyword in festival_keywords)
    
    def _create_minimal_fallback_database(self) -> Dict[str, Dict]:
        """Create a minimal festival database as fallback"""
        base_festivals = {
            # Major recurring festivals with approximate dates
            'diwali': {'month': 10, 'name': 'Diwali'},
            'holi': {'month': 3, 'name': 'Holi'},
            'dussehra': {'month': 10, 'name': 'Dussehra'},
            'ganesh_chaturthi': {'month': 8, 'name': 'Ganesh Chaturthi'},
            'navratri': {'month': 9, 'name': 'Navratri'},
            'raksha_bandhan': {'month': 8, 'name': 'Raksha Bandhan'},
            'janmashtami': {'month': 8, 'name': 'Krishna Janmashtami'},
            'karva_chauth': {'month': 10, 'name': 'Karva Chauth'},
            'dhanteras': {'month': 10, 'name': 'Dhanteras'},
            'bhai_dooj': {'month': 11, 'name': 'Bhai Dooj'},
            'makar_sankranti': {'month': 1, 'name': 'Makar Sankranti'},
            'maha_shivratri': {'month': 2, 'name': 'Maha Shivratri'},
            'ram_navami': {'month': 4, 'name': 'Ram Navami'},
            'hanuman_jayanti': {'month': 4, 'name': 'Hanuman Jayanti'},
        }
        
        fallback_festivals = {}
        current_year = datetime.now().year
        
        # Generate festivals for 50 years (25 past + 25 future)
        for year in range(current_year - 25, current_year + 26):
            for fest_key, fest_info in base_festivals.items():
                # Approximate date (15th of the month)
                try:
                    festival_date = datetime(year, fest_info['month'], 15)
                    date_str = festival_date.strftime('%Y-%m-%d')
                    
                    fallback_festivals[date_str] = {
                        'name': fest_info['name'],
                        'date': festival_date,
                        'description': f"Approximate date for {fest_info['name']}",
                        'source': 'fallback'
                    }
                except:
                    continue
        
        st.warning("Using fallback festival database with approximate dates")
        return fallback_festivals
    
    def _save_festival_database(self, festivals: Dict[str, Dict]):
        """Save festival database to JSON file"""
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            json_festivals = {}
            for date_str, festival_info in festivals.items():
                json_festival = festival_info.copy()
                json_festival['date'] = festival_info['date'].isoformat()
                json_festivals[date_str] = json_festival
            
            with open(self.festivals_json_file, 'w', encoding='utf-8') as f:
                json.dump(json_festivals, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = {
                'last_update': datetime.now().isoformat(),
                'total_festivals': len(festivals),
                'date_range': self._get_date_coverage(festivals),
                'sources': list(set(f.get('source', 'unknown') for f in festivals.values()))
            }
            
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            st.success(f"✓ Saved festival database: {len(festivals)} festivals")
            
        except Exception as e:
            st.error(f"Failed to save festival database: {e}")
    
    def _load_local_festival_database(self) -> Dict[str, Dict]:
        """Load festival database from local JSON file"""
        try:
            with open(self.festivals_json_file, 'r', encoding='utf-8') as f:
                json_festivals = json.load(f)
            
            # Convert ISO strings back to datetime objects
            festivals = {}
            for date_str, festival_info in json_festivals.items():
                festival_copy = festival_info.copy()
                festival_copy['date'] = datetime.fromisoformat(festival_info['date'])
                festivals[date_str] = festival_copy
            
            st.success(f"✓ Loaded local festival database: {len(festivals)} festivals")
            return festivals
            
        except Exception as e:
            st.error(f"Failed to load local festival database: {e}")
            return {}
    
    def _save_ics_locally(self, festivals: Dict[str, Dict]):
        """Save festivals as local ICS file for reference"""
        try:
            ics_content = self._generate_ics_content(festivals)
            
            with open(self.local_ics_file, 'w', encoding='utf-8') as f:
                f.write(ics_content)
            
            st.info(f"✓ Saved local ICS file: {self.local_ics_file}")
            
        except Exception as e:
            st.warning(f"Failed to save local ICS file: {e}")
    
    def _generate_ics_content(self, festivals: Dict[str, Dict]) -> str:
        """Generate ICS content from festival dictionary"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Goa Police//Indian Festivals Database//EN
NAME:Indian Festivals - Comprehensive Database
X-WR-CALNAME:Indian Festivals - Comprehensive Database  
DESCRIPTION:Comprehensive Indian Festivals Calendar (50+ years coverage)
X-WR-CALDESC:Comprehensive Indian Festivals Calendar (50+ years coverage)
TIMEZONE-ID:Asia/Kolkata
X-WR-TIMEZONE:Asia/Kolkata
"""
        
        for date_str, festival_info in festivals.items():
            festival_date = festival_info['date']
            festival_name = festival_info['name']
            description = festival_info.get('description', f"Indian Festival - {festival_name}")
            
            ics_content += f"""BEGIN:VEVENT
UID:{date_str}-{festival_name.replace(' ', '-').lower()}@goapolice.local
DTSTART;VALUE=DATE:{festival_date.strftime('%Y%m%d')}
DTEND;VALUE=DATE:{festival_date.strftime('%Y%m%d')}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{festival_name}
DESCRIPTION:{description}
STATUS:CONFIRMED
TRANSP:TRANSPARENT
END:VEVENT
"""
        
        ics_content += "END:VCALENDAR"
        return ics_content
    
    def _get_date_coverage(self, festivals: Dict[str, Dict]) -> str:
        """Get date range coverage of festival database"""
        if not festivals:
            return "No festivals"
        
        dates = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in festivals.keys()]
        min_date = min(dates)
        max_date = max(dates)
        
        years_coverage = max_date.year - min_date.year + 1
        return f"{min_date.year}-{max_date.year} ({years_coverage} years)"
    
    def get_festivals_in_range(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict]:
        """Get festivals within specified date range from local database"""
        # Initialize database if not already done
        if not self.festivals_cache:
            self.festivals_cache = self.initialize_festival_database()
        
        # Filter for date range
        filtered_festivals = {}
        for date_str, festival_info in self.festivals_cache.items():
            festival_date = festival_info['date']
            if start_date <= festival_date <= end_date:
                filtered_festivals[date_str] = festival_info
        
        return filtered_festivals
    
    def filter_festivals_by_crime_impact(self, festivals: Dict, call_data: pd.DataFrame, 
                                       impact_threshold: float = 1.3,
                                       min_calls_threshold: int = 3) -> Dict[str, Dict]:
        """
        Filter festivals based on actual crime data impact.
        Only keep festivals that show significant increase in calls.
        This runs dynamically for each dataset.
        """
        if call_data.empty or 'call_ts' not in call_data.columns:
            st.warning("No call data available for festival impact analysis")
            return {}
        
        # Prepare call data
        call_data = call_data.copy()
        call_data['date'] = pd.to_datetime(call_data['call_ts']).dt.date
        daily_calls = call_data.groupby('date').size()
        
        # Get date range of available data
        data_start = daily_calls.index.min()
        data_end = daily_calls.index.max()
        
        # Filter festivals to only those within data range
        festivals_in_range = {}
        for date_str, festival_info in festivals.items():
            festival_date = festival_info['date'].date()
            if data_start <= festival_date <= data_end:
                festivals_in_range[date_str] = festival_info
        
        if not festivals_in_range:
            st.info("No festivals found in the data date range")
            return {}
        
        st.info(f"Analyzing {len(festivals_in_range)} festivals within data range ({data_start} to {data_end})")
        
        # Calculate baseline call rate (excluding festival periods)
        all_dates = set(daily_calls.index)
        festival_dates = set()
        
        # Mark festival periods (festival day ± 1 day)
        for festival_info in festivals_in_range.values():
            festival_date = festival_info['date'].date()
            for delta in [-1, 0, 1]:
                extended_date = festival_date + timedelta(days=delta)
                if data_start <= extended_date <= data_end:
                    festival_dates.add(extended_date)
        
        # Calculate baseline from non-festival days
        non_festival_dates = all_dates - festival_dates
        if non_festival_dates:
            baseline_calls = daily_calls.loc[list(non_festival_dates)].mean()
        else:
            baseline_calls = daily_calls.mean()
        
        st.info(f"Baseline daily calls (non-festival): {baseline_calls:.1f}")
        
        # Analyze each festival's impact
        impactful_festivals = {}
        festival_analysis = []
        
        for date_str, festival_info in festivals_in_range.items():
            festival_date = festival_info['date'].date()
            festival_name = festival_info['name']
            
            # Get calls for festival period (day before, day of, day after)
            period_calls = []
            for delta in [-1, 0, 1]:
                check_date = festival_date + timedelta(days=delta)
                if check_date in daily_calls.index:
                    period_calls.append(daily_calls[check_date])
            
            if period_calls:
                avg_festival_calls = sum(period_calls) / len(period_calls)
                max_festival_calls = max(period_calls)
                
                # Calculate impact ratio
                impact_ratio = avg_festival_calls / baseline_calls if baseline_calls > 0 else 1
                max_impact_ratio = max_festival_calls / baseline_calls if baseline_calls > 0 else 1
                
                # Store analysis data
                festival_analysis.append({
                    'name': festival_name,
                    'date': festival_date,
                    'avg_calls': avg_festival_calls,
                    'max_calls': max_festival_calls,
                    'impact_ratio': impact_ratio,
                    'max_impact_ratio': max_impact_ratio,
                    'baseline': baseline_calls
                })
                
                # Filter based on impact thresholds
                if (impact_ratio >= impact_threshold and 
                    avg_festival_calls >= min_calls_threshold):
                    
                    # Add impact metrics to festival info
                    festival_info_copy = festival_info.copy()
                    festival_info_copy.update({
                        'impact_ratio': round(impact_ratio, 2),
                        'max_impact_ratio': round(max_impact_ratio, 2),
                        'avg_calls_during': round(avg_festival_calls, 1),
                        'max_calls_during': int(max_festival_calls),
                        'baseline_calls': round(baseline_calls, 1),
                        'impact_category': self._categorize_impact(impact_ratio)
                    })
                    
                    impactful_festivals[date_str] = festival_info_copy
        
        # Show analysis summary
        self._show_festival_analysis_summary(festival_analysis, impact_threshold)
        
        if impactful_festivals:
            st.success(f"Found {len(impactful_festivals)} festivals with significant crime impact (>{impact_threshold-1:.0%} increase)")
        else:
            st.warning(f"No festivals show significant crime impact (>{impact_threshold-1:.0%} increase) in this dataset")
        
        return impactful_festivals
    
    def _categorize_impact(self, impact_ratio: float) -> str:
        """Categorize festival impact level"""
        if impact_ratio >= 2.0:
            return 'high'
        elif impact_ratio >= 1.5:
            return 'moderate'
        else:
            return 'low'
    
    def _show_festival_analysis_summary(self, festival_analysis: List[Dict], threshold: float):
        """Show summary of festival impact analysis"""
        if not festival_analysis:
            return
        
        # Sort by impact ratio
        festival_analysis.sort(key=lambda x: x['impact_ratio'], reverse=True)
        
        # Show top impactful festivals
        with st.expander("🔍 Festival Impact Analysis Details", expanded=False):
            st.markdown("**All festivals analyzed (sorted by impact):**")
            
            for i, fest in enumerate(festival_analysis):
                impact_pct = (fest['impact_ratio'] - 1) * 100
                status = "✅ Included" if fest['impact_ratio'] >= threshold else "❌ Filtered out"
                
                st.markdown(
                    f"{i+1}. **{fest['name']}** ({fest['date']}): "
                    f"{impact_pct:+.0f}% impact "
                    f"({fest['avg_calls']:.1f} vs {fest['baseline']:.1f} baseline) "
                    f"{status}"
                )
    
    def get_festival_weeks(self, festivals: Dict) -> Dict[str, Tuple[datetime, datetime]]:
        """Convert festivals to week ranges for analysis"""
        festival_weeks = {}
        
        for date_str, festival_info in festivals.items():
            festival_date = festival_info['date']
            festival_name = festival_info['name']
            
            # Create week range (3 days before to 3 days after)
            start_date = festival_date - timedelta(days=3)
            end_date = festival_date + timedelta(days=3)
            
            festival_weeks[festival_name] = (start_date, end_date)
        
        return festival_weeks
    
    def create_festival_date_input_with_highlights(self, label: str, default_dates: List, 
                                                 festivals: Dict):
        """Create date input with festival information"""
        # Convert festivals to list for display
        festival_dates = []
        for date_str, festival_info in festivals.items():
            festival_dates.append({
                'date': festival_info['date'].date(),
                'name': festival_info['name'],
                'impact': festival_info.get('impact_ratio', 1.0)
            })
        
        # Create date input
        default_date_objects = []
        for d in default_dates:
            if hasattr(d, 'date'):
                default_date_objects.append(d.date())
            else:
                default_date_objects.append(d)
        
        selected_dates = st.date_input(
            label, 
            value=default_date_objects,
            help=f"📅 {len(festival_dates)} high-impact festivals detected in data range"
        )
        
        # Display festival info if any festivals in selected range
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            festivals_in_range = []
            
            for fest_date in festival_dates:
                if start_date <= fest_date['date'] <= end_date:
                    festivals_in_range.append(fest_date)
            
            if festivals_in_range:
                st.info(f"🎉 {len(festivals_in_range)} high-impact festivals in selected range:")
                for festival in sorted(festivals_in_range, key=lambda x: x['date'])[:5]:
                    impact_pct = (festival['impact'] - 1) * 100
                    st.caption(f"• **{festival['name']}** ({festival['date'].strftime('%b %d')}) - {impact_pct:+.0f}% impact")
                
                if len(festivals_in_range) > 5:
                    st.caption(f"... and {len(festivals_in_range) - 5} more")
        
        return selected_dates
    
    def get_database_statistics(self) -> Dict:
        """Get comprehensive database statistics"""
        stats = {
            'database_exists': False,
            'total_festivals': 0,
            'date_coverage': 'Unknown',
            'last_update': 'Never',
            'file_sizes': {},
            'sources': [],
            'festivals_by_year': {},
            'status': 'Not initialized'
        }
        
        try:
            # Check if database files exist
            files_to_check = {
                'festivals_database.json': self.festivals_json_file,
                'indian_festivals.ics': self.local_ics_file,
                'festivals_cache_metadata.json': self.cache_metadata_file
            }
            
            for name, path in files_to_check.items():
                if os.path.exists(path):
                    stats['file_sizes'][name] = f"{os.path.getsize(path) / 1024:.1f} KB"
                else:
                    stats['file_sizes'][name] = "Missing"
            
            # Load metadata if available
            if os.path.exists(self.cache_metadata_file):
                with open(self.cache_metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                stats.update({
                    'total_festivals': metadata.get('total_festivals', 0),
                    'date_coverage': metadata.get('date_range', 'Unknown'),
                    'last_update': metadata.get('last_update', 'Unknown')[:19],  # Remove microseconds
                    'sources': metadata.get('sources', [])
                })
            
            # Load festival database for detailed stats
            if os.path.exists(self.festivals_json_file):
                stats['database_exists'] = True
                
                with open(self.festivals_json_file, 'r', encoding='utf-8') as f:
                    festivals_data = json.load(f)
                
                # Count festivals by year
                year_counts = {}
                for date_str, festival_info in festivals_data.items():
                    year = date_str[:4]
                    year_counts[year] = year_counts.get(year, 0) + 1
                
                stats['festivals_by_year'] = dict(sorted(year_counts.items()))
                stats['status'] = 'Ready'
            else:
                stats['status'] = 'Database not found'
                
        except Exception as e:
            stats['status'] = f'Error: {str(e)}'
        
        return stats
    
    def show_database_status_widget(self):
        """Show database status widget in sidebar"""
        stats = self.get_database_statistics()
        
        if stats['database_exists']:
            st.sidebar.success("✅ Festival Database Ready")
            
            with st.sidebar.expander("📊 Database Statistics"):
                st.write(f"**Total Festivals:** {stats['total_festivals']}")
                st.write(f"**Coverage:** {stats['date_coverage']}")
                st.write(f"**Last Updated:** {stats['last_update']}")
                
                st.write("**File Sizes:**")
                for filename, size in stats['file_sizes'].items():
                    st.write(f"  • {filename}: {size}")
                
                if stats['festivals_by_year']:
                    years = list(stats['festivals_by_year'].keys())
                    st.write(f"**Year Range:** {years[0]} - {years[-1]}")
                    
                    # Show sample years
                    sample_years = [years[0], years[len(years)//2], years[-1]]
                    for year in sample_years:
                        count = stats['festivals_by_year'].get(year, 0)
                        st.write(f"  • {year}: {count} festivals")
        else:
            st.sidebar.warning("⚠️ Festival Database Not Found")
            st.sidebar.info("Click 'Refresh DB' to initialize")
    
    def force_refresh_database(self):
        """Force refresh the festival database"""
        st.info("Force refreshing festival database...")
        self.festivals_cache = {}
        return self.initialize_festival_database(force_refresh=True)

def initialize_ics_calendar_integration():
    """Initialize ICS calendar integration"""
    if 'ics_calendar' not in st.session_state:
        st.session_state.ics_calendar = ICSCalendarIntegration()
    
    return st.session_state.ics_calendar