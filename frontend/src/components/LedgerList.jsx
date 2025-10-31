import React from 'react';
import { FileText, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function LedgerList({ ledgers, searchTerm, onLedgerClick }) {
  if (!ledgers || ledgers.length === 0) return null;

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
    if (num > 0) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (num < 0) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  return (
    <div className="ledger-list bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow my-2">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-green-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          {ledgers.length} ledger{ledgers.length > 1 ? 's' : ''} matching '{searchTerm}'
        </h3>
      </div>

      {/* Ledger List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {ledgers.map((ledger, index) => {
          const balance = ledger.closing_balance || ledger.balance || 0;
          const name = ledger.name || 'Unknown Ledger';
          const parent = ledger.parent || 'N/A';
          
          return (
            <div
              key={index}
              onClick={() => onLedgerClick && onLedgerClick(ledger)}
              className={`bg-white rounded-lg p-3 border border-green-100 hover:border-green-300 hover:shadow-sm transition-all cursor-pointer ${
                onLedgerClick ? 'hover:bg-green-50' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 mb-1 truncate">
                    {name}
                  </h4>
                  {parent !== 'N/A' && (
                    <p className="text-xs text-gray-500 truncate">
                      {parent}
                    </p>
                  )}
                </div>
                <div className={`flex items-center gap-1 flex-shrink-0 ${getBalanceColor(balance)}`}>
                  {getBalanceIcon(balance)}
                  <span className="font-semibold text-sm whitespace-nowrap">
                    {formatBalance(balance)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer hint */}
      {onLedgerClick && (
        <p className="text-xs text-gray-500 mt-3 text-center">
          Click on a ledger to view details
        </p>
      )}
    </div>
  );
}

