import React from 'react';
import { Calendar, MapPin, Users, ExternalLink, Clock } from 'lucide-react';

export default function EventCard({ event, onAction }) {
  if (!event) return null;

  const { summary, start, end, organizer, attendees, location, hangoutLink, id } = event;

  // Format time from ISO string
  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      const options = { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true,
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      };
      return date.toLocaleString('en-US', options);
    } catch (error) {
      return isoString;
    }
  };

  const formatTimeRange = (start, end) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    
    const isSameDay = startDate.toDateString() === endDate.toDateString();
    
    if (isSameDay) {
      return `${startDate.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })} - ${endDate.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`;
    }
    
    return `${formatTime(start)} - ${formatTime(end)}`;
  };

  return (
    <div className="event-card bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow my-2">
      {/* Event Title */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-600" />
          {summary || 'Untitled Event'}
        </h3>
      </div>

      {/* Time */}
      <div className="flex items-center gap-2 mb-2 text-sm text-gray-700">
        <Clock className="w-4 h-4 text-blue-600" />
        <span>{formatTimeRange(start, end)}</span>
      </div>

      {/* Organizer */}
      {organizer && (
        <div className="flex items-center gap-2 mb-2 text-sm text-gray-700">
          <Users className="w-4 h-4 text-blue-600" />
          <span>Organizer: {organizer}</span>
        </div>
      )}

      {/* Attendees */}
      {attendees && attendees.length > 0 && (
        <div className="flex items-start gap-2 mb-2 text-sm text-gray-700">
          <Users className="w-4 h-4 text-blue-600 mt-0.5" />
          <div>
            <span className="font-medium">{attendees.length} attendee{attendees.length > 1 ? 's' : ''}:</span>
            <p className="text-gray-600">{attendees.join(', ')}</p>
          </div>
        </div>
      )}

      {/* Location */}
      {location && (
        <div className="flex items-center gap-2 mb-2 text-sm text-gray-700">
          <MapPin className="w-4 h-4 text-blue-600" />
          <span>{location}</span>
        </div>
      )}

      {/* Hangout Link */}
      {hangoutLink && (
        <div className="mb-3">
          <a
            href={hangoutLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Join Meeting
          </a>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 mt-3 pt-3 border-t border-blue-200">
        <button
          onClick={() => onAction && onAction('view', event)}
          className="flex-1 px-3 py-2 text-sm font-medium text-blue-700 bg-white border border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-colors"
        >
          View Details
        </button>
        <button
          onClick={() => onAction && onAction('reschedule', event)}
          className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Reschedule
        </button>
        <button
          onClick={() => onAction && onAction('cancel', event)}
          className="px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

