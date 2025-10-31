import { useState, useEffect, useRef } from "react";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { 
  TrendingUp, 
  TrendingDown, 
  Banknote, 
  Building2, 
  BarChart3,
  RotateCcw
} from "lucide-react";

export default function AccountingDashboard() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customDateSales, setCustomDateSales] = useState(null);
  const [endDateSales, setEndDateSales] = useState(null);
  const [yearlyComparison, setYearlyComparison] = useState(null);
  const [accountingYear, setAccountingYear] = useState("");
  const [lastEntryDate, setLastEntryDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const isInitialLoad = useRef(true);

  // Get current accounting year (April to March)
  useEffect(() => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 1-12
    
    let accountingYearStart, accountingYearEnd;
    
    if (currentMonth >= 4) {
      // Current year is April to March
      accountingYearStart = currentYear;
      accountingYearEnd = currentYear + 1;
    } else {
      // Previous year April to current year March
      accountingYearStart = currentYear - 1;
      accountingYearEnd = currentYear;
    }
    
    setAccountingYear(`${accountingYearStart}-${accountingYearEnd}`);
  }, []);

  useEffect(() => {
    if (token) {
      fetchAccountingData();
    }
  }, [token]); // Only re-fetch when token changes

  // Separate useEffect for customEndDate changes (but not on initial load)
  useEffect(() => {
    if (isInitialLoad.current) {
      isInitialLoad.current = false;
      return; // Don't fetch on initial load
    }
    if (token && customEndDate) {
      fetchAccountingData();
    }
  }, [customEndDate]); // Re-fetch when customEndDate changes

  const fetchAccountingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch yearly comparison data first to get last entry date
      const currentDate = new Date();
      const currentYear = currentDate.getFullYear();
      const currentMonth = currentDate.getMonth() + 1;
      const comparisonYear = currentMonth >= 4 ? currentYear : currentYear - 1;
      
      const comparisonResponse = await API.get("/integrations/tally/sales/yearly-comparison", {
        headers: { Authorization: `Bearer ${token}` },
        params: { 
          current_year: comparisonYear,
          custom_end_date: customEndDate || undefined // Pass customEndDate if set
        }
      });
      setYearlyComparison(comparisonResponse.data);
      
      // Extract last entry date from the response
      if (comparisonResponse.data && comparisonResponse.data.last_entry_date) {
        setLastEntryDate(comparisonResponse.data.last_entry_date);
        // Only set customEndDate if it's not already set by user
        if (!customEndDate) {
            setCustomEndDate(comparisonResponse.data.last_entry_date);
        }
      }

      // Fetch custom date sales data if we have a custom end date
      if (customEndDate) {
        const salesResponse = await API.get("/integrations/tally/sales/custom-date", {
          headers: { Authorization: `Bearer ${token}` },
          params: { custom_end_date: customEndDate }
        });
        setCustomDateSales(salesResponse.data);
        
        // Fetch sales data for the specific end date only
        const endDateResponse = await API.get("/integrations/tally/sales/specific-date", {
          headers: { Authorization: `Bearer ${token}` },
          params: { specific_date: customEndDate }
        });
        setEndDateSales(endDateResponse.data);
      }

    } catch (err) {
      console.error("Failed to fetch accounting data:", err);
      setError("Failed to load accounting data. Please ensure Tally is connected.");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Loading...';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const handleDateReset = () => {
    setCustomEndDate(lastEntryDate);
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading accounting data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingDown className="w-8 h-8 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to Load Data</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchAccountingData}
            className="minimal-button minimal-button-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="minimal-heading minimal-heading-xl text-gray-900 mb-2">
            Accounting Dashboard
          </h1>
          <p className="minimal-text text-gray-600">
            Financial overview for accounting year {accountingYear}
          </p>
        </div>

        {/* Date Range Control */}
        {yearlyComparison && yearlyComparison.comparison_data && (
          <div className="minimal-card mb-6 p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="minimal-heading minimal-heading-lg text-gray-900">
                Sales Date Range
              </h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block minimal-text-sm font-medium text-gray-700 mb-3">
                  Last Entry Date (Auto-detected)
                </label>
                <div className="minimal-text text-gray-600 bg-gray-50 px-4 py-3 rounded-lg border">
                  {formatDate(lastEntryDate)}
                </div>
              </div>
              
              <div>
                <label className="block minimal-text-sm font-medium text-gray-700 mb-3">
                  Custom End Date
                </label>
                <div className="relative">
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    onClick={handleDateReset}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    title="Reset to default date"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            
            {lastEntryDate && customEndDate && lastEntryDate !== customEndDate && (
              <div className="mt-5 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="minimal-text-sm text-blue-800">
                  <strong>Note:</strong> You're using a custom end date ({formatDate(customEndDate)}) instead of the auto-detected last entry date ({formatDate(lastEntryDate)}). 
                  This will show sales data and year-over-year comparison up to your selected date.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Custom Date Sales Summary */}
        {customDateSales && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="minimal-card p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="minimal-text-tertiary mb-2">Sales Value</p>
                  <div className="flex items-baseline space-x-3 mb-2">
                    <p className="minimal-heading minimal-heading-lg text-green-600">
                      {formatCurrency(customDateSales.total_sales || 0)}
                    </p>
                    {endDateSales && (
                      <span className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">
                        {formatCurrency(endDateSales.total_sales || 0)}
                      </span>
                    )}
                  </div>
                  <p className="minimal-text-sm text-gray-500">
                    {customDateSales.accounting_year} (Apr to {formatDate(customDateSales.end_date)})
                  </p>
                </div>
                <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center ml-4">
                  <TrendingUp className="w-7 h-7 text-green-600" />
                </div>
              </div>
            </div>

            <div className="minimal-card p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="minimal-text-tertiary mb-2">Number of Vouchers</p>
                  <div className="flex items-baseline space-x-3 mb-2">
                    <p className="minimal-heading minimal-heading-lg text-blue-600">
                      {customDateSales.voucher_count || 0}
                    </p>
                    {endDateSales && (
                      <span className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">
                        {endDateSales.voucher_count || 0}
                      </span>
                    )}
                  </div>
                  <p className="minimal-text-sm text-gray-500">
                    Sales vouchers processed
                  </p>
                </div>
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center ml-4">
                  <BarChart3 className="w-7 h-7 text-blue-600" />
                </div>
              </div>
            </div>
          </div>
        )}


        {/* Year-on-Year Comparison Table */}
        {yearlyComparison && yearlyComparison.comparison_data && (
          <div className="minimal-card mb-8 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="minimal-heading minimal-heading-lg text-gray-900">
                Year Till Date (Lakhs)
              </h3>
              <div className="flex items-center space-x-2 text-sm text-gray-500 bg-gray-50 px-3 py-2 rounded-lg">
                <BarChart3 className="w-4 h-4" />
                <span className="font-medium">{yearlyComparison.current_year}-{yearlyComparison.previous_year}</span>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-4 px-6 font-semibold text-gray-900 text-sm">Month</th>
                    <th className="text-right py-4 px-6 font-semibold text-gray-900 text-sm">{yearlyComparison.current_year}</th>
                    <th className="text-right py-4 px-6 font-semibold text-gray-900 text-sm">{yearlyComparison.previous_year}</th>
                    <th className="text-right py-4 px-6 font-semibold text-gray-900 text-sm">%</th>
                  </tr>
                </thead>
                <tbody>
                  {yearlyComparison.comparison_data.map((month, index) => {
                    const currentSalesLakhs = (month.current_year_sales || 0) / 100000;
                    const previousSalesLakhs = (month.previous_year_sales || 0) / 100000;
                    const percentageChange = month.percentage_change || 0;
                    const isPositive = percentageChange >= 0;
                    const isFutureMonth = month.is_future_month || false;
                    
                    return (
                      <tr key={index} className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${isFutureMonth ? 'opacity-60' : ''}`}>
                        <td className={`py-4 px-6 font-medium text-sm ${isFutureMonth ? 'text-gray-500' : 'text-gray-900'}`}>
                          {month.month}
                        </td>
                        <td className={`py-4 px-6 text-right font-medium text-sm ${isFutureMonth ? 'text-gray-500' : 'text-gray-900'}`}>
                          {isFutureMonth ? '-' : `₹${currentSalesLakhs.toFixed(0)}`}
                        </td>
                        <td className={`py-4 px-6 text-right font-medium text-sm ${isFutureMonth ? 'text-gray-500' : 'text-gray-900'}`}>
                          {isFutureMonth ? '-' : `₹${previousSalesLakhs.toFixed(0)}`}
                        </td>
                        <td className={`py-4 px-6 text-right font-medium text-sm ${isFutureMonth ? 'text-gray-500' : (isPositive ? 'text-green-600' : 'text-red-600')}`}>
                          {isFutureMonth ? '-' : `${percentageChange > 0 ? '+' : ''}${percentageChange.toFixed(1)}%`}
                        </td>
                      </tr>
                    );
                  })}
                  <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold">
                    <td className="py-4 px-6 font-bold text-gray-900 text-sm">Total</td>
                    <td className="py-4 px-6 text-right font-bold text-gray-900 text-sm">
                      ₹{(yearlyComparison.comparison_data
                        .filter(month => !month.is_future_month)
                        .reduce((sum, month) => sum + (month.current_year_sales || 0), 0) / 100000).toFixed(0)}
                    </td>
                    <td className="py-4 px-6 text-right font-bold text-gray-900 text-sm">
                      ₹{(yearlyComparison.comparison_data
                        .filter(month => !month.is_future_month)
                        .reduce((sum, month) => sum + (month.previous_year_sales || 0), 0) / 100000).toFixed(0)}
                    </td>
                    <td className={`py-4 px-6 text-right font-bold text-sm ${(() => {
                      const actualData = yearlyComparison.comparison_data.filter(month => !month.is_future_month);
                      const totalCurrent = actualData.reduce((sum, month) => sum + (month.current_year_sales || 0), 0);
                      const totalPrevious = actualData.reduce((sum, month) => sum + (month.previous_year_sales || 0), 0);
                      const totalPercentage = totalPrevious > 0 ? ((totalCurrent - totalPrevious) / totalPrevious) * 100 : 0;
                      return totalPercentage >= 0 ? 'text-green-600' : 'text-red-600';
                    })()}`}>
                      {(() => {
                        const actualData = yearlyComparison.comparison_data.filter(month => !month.is_future_month);
                        const totalCurrent = actualData.reduce((sum, month) => sum + (month.current_year_sales || 0), 0);
                        const totalPrevious = actualData.reduce((sum, month) => sum + (month.previous_year_sales || 0), 0);
                        const totalPercentage = totalPrevious > 0 ? ((totalCurrent - totalPrevious) / totalPrevious) * 100 : 0;
                        return `${totalPercentage > 0 ? '+' : ''}${totalPercentage.toFixed(1)}%`;
                      })()}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
