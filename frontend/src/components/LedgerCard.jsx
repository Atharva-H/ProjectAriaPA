import React from 'react';
import { FileText, TrendingUp, TrendingDown, Minus, DollarSign, Tag } from 'lucide-react';

export default function LedgerCard({ ledger, onAction }) {
  if (!ledger) return null;

  const balance = ledger.closing_balance || ledger.balance || 0;
  const openingBalance = ledger.opening_balance || 0;
  const name = ledger.name || 'Unknown Ledger';
  const parent = ledger.parent || 'N/A';

  const formatBalance = (balance) => {
    try {
      const num = parseFloat(balance) || 0;
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num);
    } catch (error) {
      return `₹${balance || '0.00'}`;
    }
  };

  const getBalanceColor = (balance) => {
    const num = parseFloat(balance) || 0;
    if (num > 0) return 'text-green-600';
    if (num < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getBalanceIcon = (balance) => {
    const num = parseFloat(balance) || 0;
    if (num > 0) return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (num < 0) return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Minus className="w-5 h-5 text-gray-600" />;
  };

  return (
    <div className="ledger-card bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow my-2">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 break-words">
              {name}
            </h3>
            {parent !== 'N/A' && (
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <Tag className="w-4 h-4" />
                <span className="truncate">{parent}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Balance Section */}
      <div className="space-y-3">
        {/* Outstanding Balance */}
        <div className="bg-white rounded-lg p-3 border border-blue-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Outstanding Balance</span>
            </div>
            <div className={`flex items-center gap-1 ${getBalanceColor(balance)}`}>
              {getBalanceIcon(balance)}
              <span className="font-bold text-lg whitespace-nowrap">
                {formatBalance(balance)}
              </span>
            </div>
          </div>
        </div>

        {/* Opening Balance */}
        <div className="bg-white rounded-lg p-3 border border-blue-100">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Opening Balance</span>
            <span className={`font-semibold text-sm ${getBalanceColor(openingBalance)} whitespace-nowrap`}>
              {formatBalance(openingBalance)}
            </span>
          </div>
        </div>
      </div>

      {/* Action Button (if provided) */}
      {onAction && (
        <div className="mt-4 pt-4 border-t border-blue-200">
          <button
            onClick={() => onAction(ledger)}
            className="w-full px-4 py-2 text-sm font-medium text-blue-700 bg-white border border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-colors"
          >
            View Details
          </button>
        </div>
      )}
    </div>
  );
}

