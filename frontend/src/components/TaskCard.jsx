// src/components/TaskCard.jsx
import React from 'react';
import { CheckCircle, Circle, Calendar, AlertTriangle, AlertCircle, Clock } from 'lucide-react';

export default function TaskCard({ task, onAction }) {
    if (!task) return null;

    const { title, deadline, is_urgent, is_important, status } = task;
    const isCompleted = status === 'completed';

    // Format deadline
    const formatDeadline = (isoString) => {
        if (!isoString) return 'No deadline';
        try {
            const date = new Date(isoString);
            return date.toLocaleString('en-US', {
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

    return (
        <div className={`task-card border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow my-2 ${isCompleted
                ? 'bg-gray-50 border-gray-200 opacity-75'
                : 'bg-white border-gray-200 dark:bg-[#343541] dark:border-white/10'
            }`}>
            <div className="flex items-start gap-3">
                {/* Checkbox / Status Icon */}
                <button
                    onClick={() => !isCompleted && onAction && onAction('mark_done', task)}
                    className={`mt-0.5 flex-shrink-0 transition-colors ${isCompleted ? 'text-green-500 cursor-default' : 'text-gray-400 hover:text-green-500'
                        }`}
                    disabled={isCompleted}
                >
                    {isCompleted ? <CheckCircle className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
                </button>

                <div className="flex-1 min-w-0">
                    {/* Title */}
                    <h3 className={`text-base font-medium mb-1 ${isCompleted ? 'text-gray-500 line-through' : 'text-gray-900 dark:text-gray-100'
                        }`}>
                        {title || 'Untitled Task'}
                    </h3>

                    {/* Details Row */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mt-2">
                        {/* Deadline */}
                        {deadline && (
                            <div className="flex items-center gap-1.5">
                                <Calendar className="w-3.5 h-3.5" />
                                <span>{formatDeadline(deadline)}</span>
                            </div>
                        )}

                        {/* Tags */}
                        <div className="flex items-center gap-2">
                            {is_urgent && (
                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 font-medium">
                                    <AlertCircle className="w-3 h-3" />
                                    Urgent
                                </span>
                            )}
                            {is_important && (
                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 font-medium">
                                    <AlertTriangle className="w-3 h-3" />
                                    Important
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Action Button (if not completed) */}
            {!isCompleted && (
                <div className="mt-3 pl-8">
                    <button
                        onClick={() => onAction && onAction('mark_done', task)}
                        className="text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                    >
                        Mark as Done
                    </button>
                </div>
            )}
        </div>
    );
}
