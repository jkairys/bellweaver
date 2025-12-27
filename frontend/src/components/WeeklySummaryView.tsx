import { useState, useMemo, useCallback } from 'react';
import type {
  WeeklySummaryResponse,
  RelevantEvent,
  EventHighlight,
} from '../types/api';
import { getWeeklySummary } from '../services/api';
import './WeeklySummaryView.css';

function WeeklySummaryView() {
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // Default to current week's Monday
    const today = new Date();
    const dayOfWeek = today.getDay();
    const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust for Monday
    const monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    return monday.toISOString().split('T')[0];
  });

  const [summary, setSummary] = useState<WeeklySummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch summary when date changes
  const fetchSummary = useCallback(async (weekStart: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWeeklySummary(weekStart);
      setSummary(data);
    } catch (err) {
      setError((err as Error).message);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle date selection - snap to Monday
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = new Date(e.target.value);
    // Adjust to nearest Monday
    const dayOfWeek = date.getDay();
    const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    date.setDate(date.getDate() + diff);
    const mondayStr = date.toISOString().split('T')[0];
    setSelectedDate(mondayStr);
  };

  // Load summary on button click
  const handleLoadSummary = () => {
    fetchSummary(selectedDate);
  };

  // Format date range for display
  const dateRange = useMemo(() => {
    if (!summary) return null;
    const start = new Date(summary.week_start);
    const end = new Date(summary.week_end);
    return `${start.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })} - ${end.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })}`;
  }, [summary]);

  // Group events by day
  const eventsByDay = useMemo(() => {
    if (!summary?.relevant_events) return {};

    const grouped: Record<string, RelevantEvent[]> = {};
    summary.relevant_events.forEach((event) => {
      const dateKey = new Date(event.start).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      });
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(event);
    });
    return grouped;
  }, [summary]);

  return (
    <div className="weekly-summary-view">
      <div className="summary-header">
        <h2>Weekly Summary</h2>
        <div className="date-picker-section">
          <label htmlFor="week-picker">Week starting:</label>
          <input
            type="date"
            id="week-picker"
            value={selectedDate}
            onChange={handleDateChange}
            className="date-picker"
          />
          <button
            onClick={handleLoadSummary}
            className="load-button"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Generate Summary'}
          </button>
        </div>
      </div>

      {error && (
        <div className="summary-error">
          <p>Error: {error}</p>
        </div>
      )}

      {loading && (
        <div className="summary-loading">
          <p>Generating your weekly summary with AI...</p>
        </div>
      )}

      {summary && !loading && (
        <>
          {/* Summary Text */}
          <div className="summary-overview">
            <div className="week-range-badge">{dateRange}</div>
            {summary.children_included.length > 0 && (
              <p className="children-info">
                Summary for: {summary.children_included.join(', ')}
              </p>
            )}
            <p className="summary-text">{summary.summary}</p>
          </div>

          {/* Highlights Section */}
          {summary.highlights.length > 0 && (
            <div className="highlights-section">
              <h3>Highlights This Week</h3>
              <div className="highlights-list">
                {summary.highlights.map((highlight: EventHighlight) => (
                  <div key={highlight.id} className="highlight-card">
                    <h4>{highlight.title}</h4>
                    <p className="highlight-reason">{highlight.why_notable}</p>
                    {highlight.action_needed && (
                      <p className="action-needed">
                        Action needed: {highlight.action_needed}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recurring Events Section */}
          {summary.recurring_events.length > 0 && (
            <div className="recurring-section">
              <h3>Regular Activities</h3>
              <div className="recurring-list">
                {summary.recurring_events.map((group, idx) => (
                  <div key={idx} className="recurring-item">
                    <span className="recurring-pattern">{group.pattern}</span>
                    <span className="recurring-count">
                      {group.count}x this week
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Daily Events */}
          <div className="daily-events-section">
            <h3>Events by Day</h3>
            {Object.keys(eventsByDay).length === 0 ? (
              <p className="no-events">No events scheduled for this week</p>
            ) : (
              Object.entries(eventsByDay).map(([dateKey, events]) => (
                <div key={dateKey} className="day-group">
                  <h4 className="day-title">{dateKey}</h4>
                  <div className="day-events">
                    {events.map((event) => (
                      <div key={event.id} className="summary-event-card">
                        <div className="event-time-col">
                          {event.all_day ? (
                            <span className="all-day-tag">All Day</span>
                          ) : (
                            <span className="event-time">
                              {new Date(event.start).toLocaleTimeString([], {
                                hour: 'numeric',
                                minute: '2-digit',
                              })}
                            </span>
                          )}
                        </div>
                        <div className="event-info-col">
                          <h5 className="event-title">{event.title}</h5>
                          <p className="event-child">For: {event.child_name}</p>
                          <p className="event-relevance">
                            {event.relevance_reason}
                          </p>
                          {event.location && (
                            <p className="event-location">
                              Location: {event.location}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {!summary && !loading && !error && (
        <div className="summary-empty">
          <p>
            Select a week and click "Generate Summary" to see your weekly
            overview.
          </p>
        </div>
      )}
    </div>
  );
}

export default WeeklySummaryView;
