import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Clock, Calendar as CalendarIcon } from 'lucide-react';

export default function ConfirmationPrompt({ prompt, onConfirm, onCancel }) {
  const [isProcessing, setIsProcessing] = useState(false);

  if (!prompt) return null;

  const { 
    action, 
    title, 
    datetime, 
    description, 
    duration_minutes, 
    conflict, 
    free_slots_formatted = [],
    free_slots = [], // Support both old and new format
    parsed_start,
    parsed_end 
  } = prompt;

  // Use formatted slots if available, otherwise fall back to old format
  const slotsToDisplay = free_slots_formatted.length > 0 ? free_slots_formatted : free_slots;

  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return isoString;
    }
  };

  const handleConfirmAnyway = () => {
    if (isProcessing) return;
    setIsProcessing(true);
    // Option 1 = Create anyway
    onConfirm({ action: 'confirm_anyway', option: 1 });
  };

  const handleSlotSelection = (slotIndex) => {
    if (isProcessing) return;
    setIsProcessing(true);
    // Options start from 2 (since 1 is "Create anyway")
    // slotIndex is 0-based, so option number = slotIndex + 2
    const optionNumber = slotIndex + 2;
    onConfirm({ action: 'choose_slot', slotIndex, option: optionNumber });
  };

  const handleCancel = () => {
    if (isProcessing) return;
    onCancel();
  };

  return (
    <div className={`confirmation-prompt bg-yellow-50 border-2 border-yellow-300 rounded-xl p-4 my-2 transition-all duration-300 ${
      isProcessing ? 'opacity-60 pointer-events-none grayscale' : ''
    }`}>
      {/* Warning Icon */}
      <div className="flex items-start gap-3 mb-4">
        <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">Schedule Conflict</h3>
          <p className="text-sm text-gray-700">
            You're already busy with <span className="font-medium text-red-600">{conflict}</span>
          </p>
        </div>
      </div>

      {/* Proposed Event Details */}
      <div className="bg-white rounded-lg p-3 mb-4 border border-yellow-200">
        <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <CalendarIcon className="w-4 h-4 text-blue-600" />
          Proposed Event
        </h4>
        <div className="space-y-1 text-sm">
          <p className="text-gray-900"><strong>{title || 'Untitled Event'}</strong></p>
          <p className="text-gray-600 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            {formatTime(parsed_start || datetime)}
          </p>
          {description && (
            <p className="text-gray-600">{description}</p>
          )}
        </div>
      </div>

      {/* Action Selection */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-gray-900">What would you like to do?</p>

        {/* Option 1: Create anyway - Clickable button that immediately submits */}
        <button
          onClick={handleConfirmAnyway}
          disabled={isProcessing}
          className="w-full flex items-center justify-between p-3 bg-yellow-100 hover:bg-yellow-200 border border-yellow-400 rounded-lg transition-colors text-left group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-yellow-700" />
            <span className="font-medium text-gray-900">Create anyway (overlapping)</span>
          </div>
          <CheckCircle className="w-5 h-5 text-yellow-700 group-hover:scale-110 transition-transform" />
        </button>

        {/* Free Slots - Each button immediately submits on click */}
        {slotsToDisplay && slotsToDisplay.length > 0 && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-900 mb-2">Available free slots:</p>
            <div className="space-y-2">
              {slotsToDisplay.map((slot, index) => {
                // Option numbers start from 2 (since 1 is "Create anyway")
                const optionNumber = index + 2;
                const slotText = typeof slot === 'string' ? slot : slot.formatted || slot;
                
                return (
                  <button
                    key={index}
                    onClick={() => handleSlotSelection(index)}
                    disabled={isProcessing}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed ${
                      isProcessing
                        ? 'bg-gray-100 border-gray-300'
                        : 'bg-white border-gray-300 hover:bg-green-50 hover:border-green-300 active:bg-green-100'
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 font-semibold text-xs ${
                      isProcessing
                        ? 'border-gray-400 text-gray-400'
                        : 'border-blue-600 text-blue-600'
                    }`}>
                      {optionNumber}
                    </div>
                    <div className="flex-1">
                      <span className="text-sm font-medium text-gray-900">{slotText}</span>
                    </div>
                    {!isProcessing && (
                      <CheckCircle className="w-5 h-5 text-green-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Cancel Button */}
        <button
          onClick={handleCancel}
          disabled={isProcessing}
          className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4"
        >
          Cancel
        </button>
      </div>

      {/* Processing indicator */}
      {isProcessing && (
        <div className="mt-3 text-center">
          <p className="text-sm text-gray-600 italic">Processing your selection...</p>
        </div>
      )}
    </div>
  );
}

