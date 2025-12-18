# app/services/accounting/tally_sql_service.py

import asyncpg
import asyncio
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import logging
from contextlib import asynccontextmanager
from .sql_validator import sql_validator
from .tally_query_builder import tally_query_builder

logger = logging.getLogger("ProjectAria.TallySQLService")


class TallySQLService:
    """Service for executing SQL queries against Tally PostgreSQL databases."""
    
    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None):
        """Initialize with database connection parameters."""
        # Set default credentials for Tally integration
        self.host = host or "localhost"
        self.port = port or 5432
        self.user = user or "postgres"
        self.password = password or "12345678"
        self._connection_pool = None
        self._max_connections = 10
        self._min_connections = 2
    
    async def initialize(self):
        """Initialize the SQL service connection pool."""
        try:
            await self.initialize_pool()
            logger.info("✅ Tally SQL service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Tally SQL service: {str(e)}")
            raise

    async def initialize_pool(self):
        """Initialize the connection pool."""
        if self._connection_pool is None:
            try:
                self._connection_pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    min_size=self._min_connections,
                    max_size=self._max_connections,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'ProjectAria.TallySQL',
                        'timezone': 'UTC'
                    }
                )
                logger.info(f"✅ PostgreSQL connection pool initialized: {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize connection pool: {str(e)}")
                raise
    
    async def close_pool(self):
        """Close the connection pool."""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            logger.info("🔌 PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self, database_name: str):
        """Get a database connection from the pool."""
        if not self._connection_pool:
            await self.initialize_pool()
        
        connection = None
        try:
            # Create a new connection to the specific database
            connection = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database_name,
                command_timeout=60
            )
            yield connection
        except Exception as e:
            logger.error(f"❌ Database connection error for {database_name}: {str(e)}")
            raise
        finally:
            if connection:
                await connection.close()
    
    async def test_connection(self, database_name: str) -> Dict:
        """Test connection to a specific Tally database."""
        try:
            async with self.get_connection(database_name) as conn:
                # Test with a simple query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info(f"✅ Database connection test successful: {database_name}")
                    return {"success": True, "message": "Connection successful"}
                else:
                    return {"success": False, "message": "Unexpected query result"}
        except Exception as e:
            logger.error(f"❌ Database connection test failed for {database_name}: {str(e)}")
            return {"success": False, "message": f"Connection failed: {str(e)}"}
    
    async def execute_query(self, database_name: str, query: str, params: List = None) -> Dict:
        """
        Execute a SQL query against the specified database.
        
        Args:
            database_name: Name of the database to query
            query: SQL query string
            params: Query parameters for parameterized queries
            
        Returns:
            Dictionary with query results
        """
        try:
            # Validate the query first
            is_valid, error = sql_validator.validate_query(query)
            if not is_valid:
                logger.error(f"❌ Invalid query rejected: {error}")
                return {"success": False, "message": f"Query validation failed: {error}"}
            
            # Validate table access
            table_valid, table_error = sql_validator.validate_table_access(query)
            if not table_valid:
                logger.error(f"❌ Table access denied: {table_error}")
                return {"success": False, "message": f"Table access denied: {table_error}"}
            
            async with self.get_connection(database_name) as conn:
                logger.info(f"🔍 Executing query on {database_name}: {query[:100]}...")
                
                # Execute the query
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)
                
                # Convert rows to dictionaries
                results = []
                for row in rows:
                    results.append(dict(row))
                
                logger.info(f"✅ Query executed successfully: {len(results)} rows returned")
                return {
                    "success": True,
                    "data": results,
                    "count": len(results)
                }
                
        except Exception as e:
            logger.error(f"❌ Query execution failed: {str(e)}")
            return {"success": False, "message": f"Query execution failed: {str(e)}"}
    
    async def get_ledgers(self, database_name: str, filters: Dict = None) -> Dict:
        """Get ledgers from the database."""
        try:
            query = tally_query_builder.build_ledgers_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "ledgers": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get ledgers: {str(e)}")
            return {"success": False, "message": f"Failed to get ledgers: {str(e)}"}
    
    async def get_vouchers(self, database_name: str, filters: Dict = None) -> Dict:
        """Get vouchers from the database with total count."""
        try:
            # Get the main query
            query = tally_query_builder.build_vouchers_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                # Get total count (without LIMIT/OFFSET)
                count_filters = filters.copy() if filters else {}
                count_filters.pop('limit', None)
                count_filters.pop('offset', None)
                
                count_query = tally_query_builder.build_vouchers_query(count_filters)
                # Replace SELECT with COUNT
                count_query = count_query.replace(
                    "SELECT \n            v.date,\n            v.voucher_type,\n            v.voucher_number,\n            v.party_name,\n            v.narration,\n            v.is_invoice,\n            v.is_accounting_voucher,\n            v.is_inventory_voucher,\n            v.is_order_voucher,\n            a.ledger,\n            a.amount",
                    "SELECT COUNT(*)"
                )
                count_query = count_query.split("ORDER BY")[0]  # Remove ORDER BY for count
                
                count_result = await self.execute_query(database_name, count_query)
                total_count = count_result.get("data", [{}])[0].get("count", 0) if count_result.get("success") else 0
                
                return {
                    "success": True,
                    "vouchers": result.get("data", []),
                    "count": result.get("count", 0),
                    "total_count": total_count
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get vouchers: {str(e)}")
            return {"success": False, "message": f"Failed to get vouchers: {str(e)}"}
    
    async def get_ledger_balance(self, database_name: str, ledger_name: str = None, 
                                as_of_date: str = None) -> Dict:
        """Get ledger balance calculation."""
        try:
            query = tally_query_builder.build_ledger_balance_query(ledger_name, as_of_date)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "balances": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get ledger balance: {str(e)}")
            return {"success": False, "message": f"Failed to get ledger balance: {str(e)}"}
    
    async def get_stock_items(self, database_name: str, filters: Dict = None) -> Dict:
        """Get stock items from the database."""
        try:
            query = tally_query_builder.build_stock_items_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "items": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get stock items: {str(e)}")
            return {"success": False, "message": f"Failed to get stock items: {str(e)}"}
    
    async def get_parties(self, database_name: str, filters: Dict = None) -> Dict:
        """Get parties (debtors/creditors) from the database."""
        try:
            query = tally_query_builder.build_parties_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "parties": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get parties: {str(e)}")
            return {"success": False, "message": f"Failed to get parties: {str(e)}"}
    
    async def get_inventory(self, database_name: str, filters: Dict = None) -> Dict:
        """Get inventory transactions from the database."""
        try:
            query = tally_query_builder.build_inventory_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "inventory": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get inventory: {str(e)}")
            return {"success": False, "message": f"Failed to get inventory: {str(e)}"}
    
    async def get_financial_summary(self, database_name: str) -> Dict:
        """Get financial summary including payables and receivables calculated from transactions."""
        try:
            # Calculate receivables from transactions (Current Assets -> Sundry Debtors)
            receivables_query = """
            SELECT 
                SUM(l.opening_balance + COALESCE(transaction_total, 0)) as total_receivables,
                COUNT(*) as count
            FROM mst_ledger l
            LEFT JOIN (
                SELECT 
                    a.ledger,
                    SUM(a.amount) as transaction_total
                FROM trn_accounting a
                JOIN trn_voucher v ON a.guid = v.guid
                WHERE (v.is_order_voucher = 0 OR v.is_order_voucher IS NULL)
                AND (v.is_inventory_voucher = 0 OR v.is_inventory_voucher IS NULL)
                GROUP BY a.ledger
            ) t ON l.name = t.ledger
            WHERE l.parent = 'Sundry Debtors'
            AND (l.opening_balance + COALESCE(t.transaction_total, 0)) > 0
            """
            
            # Calculate payables from transactions (Current Liabilities -> Sundry Creditors)
            payables_query = """
            SELECT 
                SUM(l.opening_balance + COALESCE(transaction_total, 0)) as total_payables,
                COUNT(*) as count
            FROM mst_ledger l
            LEFT JOIN (
                SELECT 
                    a.ledger,
                    SUM(a.amount) as transaction_total
                FROM trn_accounting a
                JOIN trn_voucher v ON a.guid = v.guid
                WHERE (v.is_order_voucher = 0 OR v.is_order_voucher IS NULL)
                AND (v.is_inventory_voucher = 0 OR v.is_inventory_voucher IS NULL)
                GROUP BY a.ledger
            ) t ON l.name = t.ledger
            WHERE l.parent = 'Sundry Creditors'
            AND (l.opening_balance + COALESCE(t.transaction_total, 0)) > 0
            """
            
            # Calculate cash and bank balances from transactions
            cash_bank_query = """
            SELECT 
                SUM(CASE WHEN l.name LIKE '%Cash%' THEN (l.opening_balance + COALESCE(t.transaction_total, 0)) ELSE 0 END) as cash_balance,
                SUM(CASE WHEN l.name LIKE '%Bank%' THEN (l.opening_balance + COALESCE(t.transaction_total, 0)) ELSE 0 END) as bank_balance
            FROM mst_ledger l
            LEFT JOIN (
                SELECT 
                    a.ledger,
                    SUM(a.amount) as transaction_total
                FROM trn_accounting a
                JOIN trn_voucher v ON a.guid = v.guid
                WHERE (v.is_order_voucher = 0 OR v.is_order_voucher IS NULL)
                AND (v.is_inventory_voucher = 0 OR v.is_inventory_voucher IS NULL)
                GROUP BY a.ledger
            ) t ON l.name = t.ledger
            WHERE (l.name LIKE '%Cash%' OR l.name LIKE '%Bank%')
            AND (l.opening_balance + COALESCE(t.transaction_total, 0)) > 0
            """
            
            receivables_result = await self.execute_query(database_name, receivables_query)
            payables_result = await self.execute_query(database_name, payables_query)
            cash_bank_result = await self.execute_query(database_name, cash_bank_query)
            
            if all([receivables_result.get("success"), payables_result.get("success"), cash_bank_result.get("success")]):
                receivables_data = receivables_result.get("data", [{}])[0]
                payables_data = payables_result.get("data", [{}])[0]
                cash_bank_data = cash_bank_result.get("data", [{}])[0]
                
                return {
                    "success": True,
                    "summary": {
                        "receivables": {
                            "total": float(receivables_data.get("total_receivables") or 0),
                            "count": int(receivables_data.get("count") or 0)
                        },
                        "payables": {
                            "total": float(payables_data.get("total_payables") or 0),
                            "count": int(payables_data.get("count") or 0)
                        },
                        "cash_bank": {
                            "cash": float(cash_bank_data.get("cash_balance") or 0),
                            "bank": float(cash_bank_data.get("bank_balance") or 0)
                        }
                    }
                }
            else:
                return {"success": False, "message": "Failed to fetch financial summary data"}
                
        except Exception as e:
            logger.error(f"❌ Failed to get financial summary: {str(e)}")
            return {"success": False, "message": f"Failed to get financial summary: {str(e)}"}
    
    async def get_bill_tracking(self, database_name: str, filters: Dict = None) -> Dict:
        """Get bill tracking information."""
        try:
            query = tally_query_builder.build_bill_tracking_query(filters)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "bills": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get bill tracking: {str(e)}")
            return {"success": False, "message": f"Failed to get bill tracking: {str(e)}"}
    

    async def get_specific_date_sales(self, database_name: str, specific_date: str) -> Dict:
        """Get sales data for a specific date only."""
        try:
            from datetime import datetime
            
            # Parse the specific date
            try:
                target_date = datetime.strptime(specific_date, "%Y-%m-%d").date()
            except ValueError:
                return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
            
            # Query for sales data for that specific date only
            sales_query = """
            SELECT 
                COUNT(DISTINCT trn_voucher.guid) as voucher_count,
                SUM(CASE WHEN trn_accounting.amount <= 0 THEN -trn_accounting.amount ELSE 0 END) as total_sales
            FROM trn_voucher
            JOIN trn_accounting ON trn_voucher.guid = trn_accounting.guid
            JOIN mst_vouchertype ON trn_voucher.voucher_type = mst_vouchertype.name
            WHERE mst_vouchertype.parent = 'Sales'
            AND trn_voucher.date = $1
            AND (trn_voucher.is_order_voucher = 0 OR trn_voucher.is_order_voucher IS NULL)
            AND (trn_voucher.is_inventory_voucher = 0 OR trn_voucher.is_inventory_voucher IS NULL)
            AND trn_accounting.amount <= 0
            """
            
            result = await self.execute_query(database_name, sales_query, [target_date])
            
            if result.get("success"):
                data = result.get("data", [{}])[0]
                voucher_count = data.get("voucher_count", 0) or 0
                total_sales = data.get("total_sales", 0) or 0
                
                return {
                    "success": True,
                    "date": specific_date,
                    "voucher_count": voucher_count,
                    "total_sales": total_sales
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get specific date sales: {str(e)}")
            return {"success": False, "message": f"Failed to get specific date sales: {str(e)}"}

    async def get_custom_date_sales(self, database_name: str, custom_end_date: str) -> Dict:
        """Get sales data for a custom date range (from April 1st to the custom date)."""
        try:
            from datetime import datetime
            
            # Parse the custom end date
            try:
                end_date = datetime.strptime(custom_end_date, "%Y-%m-%d").date()
            except ValueError:
                return {"success": False, "message": "Invalid custom end date format. Use YYYY-MM-DD"}
            
            # Determine the accounting year and start date
            if end_date.month >= 4:  # April to December
                accounting_year = end_date.year
                start_date = datetime(accounting_year, 4, 1).date()
            else:  # January to March (next year in accounting year)
                accounting_year = end_date.year - 1
                start_date = datetime(accounting_year, 4, 1).date()
            
            # Query for sales data and voucher count
            sales_query = """
            SELECT 
                COUNT(DISTINCT trn_voucher.guid) as voucher_count,
                SUM(CASE WHEN trn_accounting.amount <= 0 THEN -trn_accounting.amount ELSE 0 END) as total_sales
            FROM trn_voucher
            JOIN trn_accounting ON trn_voucher.guid = trn_accounting.guid
            JOIN mst_vouchertype ON trn_voucher.voucher_type = mst_vouchertype.name
            WHERE mst_vouchertype.parent = 'Sales'
            AND trn_voucher.date >= $1
            AND trn_voucher.date <= $2
            AND (trn_voucher.is_order_voucher = 0 OR trn_voucher.is_order_voucher IS NULL)
            AND (trn_voucher.is_inventory_voucher = 0 OR trn_voucher.is_inventory_voucher IS NULL)
            AND trn_accounting.amount <= 0
            """
            
            result = await self.execute_query(database_name, sales_query, [start_date, end_date])
            
            if result.get("success"):
                data = result.get("data", [{}])[0]
                voucher_count = data.get("voucher_count", 0) or 0
                total_sales = data.get("total_sales", 0) or 0
                
                return {
                    "success": True,
                    "accounting_year": f"{accounting_year}-{accounting_year + 1}",
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "voucher_count": voucher_count,
                    "total_sales": total_sales
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get custom date sales: {str(e)}")
            return {"success": False, "message": f"Failed to get custom date sales: {str(e)}"}

    async def get_yearly_sales_comparison(self, database_name: str, current_year: int, custom_end_date: str = None) -> Dict:
        """Get year-on-year sales comparison data."""
        try:
            from datetime import datetime
            
            # First, find the last entry date in the current year's data
            last_entry_query = """
            SELECT MAX(trn_voucher.date) as last_date
            FROM trn_voucher
            JOIN trn_accounting ON trn_voucher.guid = trn_accounting.guid
            JOIN mst_vouchertype ON trn_voucher.voucher_type = mst_vouchertype.name
            WHERE mst_vouchertype.parent = 'Sales'
            AND trn_voucher.date >= $1
            AND trn_voucher.date <= $2
            AND (trn_voucher.is_order_voucher = 0 OR trn_voucher.is_order_voucher IS NULL)
            AND (trn_voucher.is_inventory_voucher = 0 OR trn_voucher.is_inventory_voucher IS NULL)
            AND trn_accounting.amount <= 0
            """
            
            # Get the last entry date for current year
            current_year_start = datetime(current_year, 4, 1).date()
            current_year_max_end = datetime(current_year + 1, 3, 31).date()
            
            last_entry_result = await self.execute_query(database_name, last_entry_query, [current_year_start, current_year_max_end])
            
            if not last_entry_result.get("success") or not last_entry_result.get("data"):
                return {"success": False, "message": "No sales data found for current year"}
            
            last_entry_date = last_entry_result.get("data")[0].get("last_date")
            if not last_entry_date:
                return {"success": False, "message": "No sales data found for current year"}
            
            # Determine the comparison years and end dates based on custom end date or last entry date
            comparison_year_for_query = current_year # Default to the year passed in
            
            if custom_end_date:
                try:
                    custom_date = datetime.strptime(custom_end_date, "%Y-%m-%d").date()
                    
                    # Determine which accounting year the custom date falls into
                    if custom_date.month >= 4:  # April to December
                        comparison_year_for_query = custom_date.year
                    else:  # January to March
                        comparison_year_for_query = custom_date.year - 1
                    
                    current_year_end = custom_date
                    previous_year_end = datetime(comparison_year_for_query - 1, custom_date.month, custom_date.day).date()
                    
                except ValueError:
                    return {"success": False, "message": "Invalid custom end date format. Use YYYY-MM-DD"}
            else:
                current_year_end = last_entry_date
                previous_year_end = datetime(current_year - 1, last_entry_date.month, last_entry_date.day).date()
            
            current_year_start = datetime(comparison_year_for_query, 4, 1).date()
            previous_year_start = datetime(comparison_year_for_query - 1, 4, 1).date()
            
            # Get current year sales data
            current_year_query = """
            SELECT 
                EXTRACT(MONTH FROM trn_voucher.date) as month_num,
                TO_CHAR(DATE_TRUNC('month', trn_voucher.date), 'Mon') as month_name,
                SUM(CASE WHEN trn_accounting.amount <= 0 THEN -trn_accounting.amount ELSE 0 END) as total_sales
            FROM trn_voucher
            JOIN trn_accounting ON trn_voucher.guid = trn_accounting.guid
            JOIN mst_vouchertype ON trn_voucher.voucher_type = mst_vouchertype.name
            WHERE mst_vouchertype.parent = 'Sales'
            AND trn_voucher.date >= $1
            AND trn_voucher.date <= $2
            AND (trn_voucher.is_order_voucher = 0 OR trn_voucher.is_order_voucher IS NULL)
            AND (trn_voucher.is_inventory_voucher = 0 OR trn_voucher.is_inventory_voucher IS NULL)
            AND trn_accounting.amount <= 0
            GROUP BY EXTRACT(MONTH FROM trn_voucher.date), TO_CHAR(DATE_TRUNC('month', trn_voucher.date), 'Mon')
            ORDER BY EXTRACT(MONTH FROM trn_voucher.date)
            """
            
            # Get previous year sales data
            previous_year_query = """
            SELECT 
                EXTRACT(MONTH FROM trn_voucher.date) as month_num,
                TO_CHAR(DATE_TRUNC('month', trn_voucher.date), 'Mon') as month_name,
                SUM(CASE WHEN trn_accounting.amount <= 0 THEN -trn_accounting.amount ELSE 0 END) as total_sales
            FROM trn_voucher
            JOIN trn_accounting ON trn_voucher.guid = trn_accounting.guid
            JOIN mst_vouchertype ON trn_voucher.voucher_type = mst_vouchertype.name
            WHERE mst_vouchertype.parent = 'Sales'
            AND trn_voucher.date >= $1
            AND trn_voucher.date <= $2
            AND (trn_voucher.is_order_voucher = 0 OR trn_voucher.is_order_voucher IS NULL)
            AND (trn_voucher.is_inventory_voucher = 0 OR trn_voucher.is_inventory_voucher IS NULL)
            AND trn_accounting.amount <= 0
            GROUP BY EXTRACT(MONTH FROM trn_voucher.date), TO_CHAR(DATE_TRUNC('month', trn_voucher.date), 'Mon')
            ORDER BY EXTRACT(MONTH FROM trn_voucher.date)
            """
            
            # Execute both queries
            current_result = await self.execute_query(database_name, current_year_query, [current_year_start, current_year_end])
            previous_result = await self.execute_query(database_name, previous_year_query, [previous_year_start, previous_year_end])
            
            if current_result.get("success") and previous_result.get("success"):
                # Process the data to create comparison
                current_data = {row['month_num']: row for row in current_result.get("data", [])}
                previous_data = {row['month_num']: row for row in previous_result.get("data", [])}
                
                # Create comparison data for all 12 months (April to March)
                comparison_data = []
                month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
                
                # Determine which months are future based on the end date
                end_month = current_year_end.month
                end_day = current_year_end.day
                
                for i, month_name in enumerate(month_names):
                    # Map accounting year months to calendar months
                    if i < 9:  # Apr to Dec (months 4-12)
                        month_num = i + 4
                    else:  # Jan to Mar (months 1-3)
                        month_num = i - 8
                    
                    current_sales = current_data.get(month_num, {}).get('total_sales', 0) or 0
                    previous_sales = previous_data.get(month_num, {}).get('total_sales', 0) or 0
                    
                    # Check if this is a future month based on the end date
                    is_future_month = False
                    
                    # For accounting year (Apr to Mar), determine if month is future
                    if month_num >= 4:  # Apr to Dec
                        # If end date is in Apr-Dec, months after end date are future
                        if end_month >= 4:  # End date is in Apr-Dec
                            if month_num > end_month or (month_num == end_month and end_day < 1):
                                is_future_month = True
                        else:  # End date is in Jan-Mar, so all Apr-Dec are past (not future)
                            is_future_month = False
                    else:  # Jan to Mar (next year in accounting year)
                        # If end date is in Apr-Dec, then Jan-Mar are future
                        # If end date is in Jan-Mar, then only months after end date are future
                        if end_month >= 4:  # End date is in Apr-Dec, so Jan-Mar are future
                            is_future_month = True
                        else:  # End date is in Jan-Mar, check if this month is after end date
                            if month_num > end_month or (month_num == end_month and end_day < 1):
                                is_future_month = True
                    
                    # Calculate percentage change only for actual data (not future months)
                    percentage_change = 0
                    if not is_future_month:
                        if previous_sales > 0:
                            percentage_change = ((current_sales - previous_sales) / previous_sales) * 100
                        elif current_sales > 0:
                            percentage_change = 100  # 100% increase from 0
                    
                    # Format month name with brackets for future months
                    display_month = f"({month_name})" if is_future_month else month_name
                    
                    comparison_data.append({
                        'month': display_month,
                        'month_num': month_num,
                        'current_year_sales': current_sales,
                        'previous_year_sales': previous_sales,
                        'percentage_change': percentage_change,
                        'is_future_month': is_future_month
                    })
                
                return {
                    "success": True,
                    "comparison_data": comparison_data,
                    "current_year": comparison_year_for_query, # Return the dynamically determined current year
                    "previous_year": comparison_year_for_query - 1, # Return the dynamically determined previous year
                    "last_entry_date": last_entry_date.strftime("%Y-%m-%d"),
                    "current_year_end": current_year_end.strftime("%Y-%m-%d"),
                    "previous_year_end": previous_year_end.strftime("%Y-%m-%d")
                }
            else:
                return {"success": False, "message": "Failed to fetch yearly comparison data"}
                
        except Exception as e:
            logger.error(f"❌ Failed to get yearly sales comparison: {str(e)}")
            return {"success": False, "message": f"Failed to get yearly sales comparison: {str(e)}"}
    
    async def get_custom_data(self, database_name: str, table_name: str, 
                             fields: List[str], filters: Dict = None,
                             joins: List[Dict] = None, order_by: str = None,
                             limit: int = None) -> Dict:
        """Get custom data using flexible query builder."""
        try:
            query = tally_query_builder.build_custom_query(
                base_table=table_name,
                fields=fields,
                joins=joins,
                filters=filters,
                order_by=order_by,
                limit=limit
            )
            
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": result.get("data", []),
                    "count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get custom data: {str(e)}")
            return {"success": False, "message": f"Failed to get custom data: {str(e)}"}
    
    async def get_sales(self, database_name: str, party_name: str = None, 
                       from_date: str = None, to_date: str = None) -> Dict:
        """Calculate total sales for a specific party within a date range."""
        try:
            query = tally_query_builder.build_sales_query(party_name, from_date, to_date)
            result = await self.execute_query(database_name, query)
            
            if result.get("success"):
                data = result.get("data", [{}])
                if data and len(data) > 0:
                    total_sales = data[0].get("total_sales", 0) or 0
                    voucher_count = data[0].get("voucher_count", 0) or 0
                    return {
                        "success": True,
                        "total_sales": float(total_sales) if isinstance(total_sales, Decimal) else total_sales,
                        "voucher_count": int(voucher_count),
                        "party_name": party_name,
                        "from_date": from_date,
                        "to_date": to_date
                    }
                else:
                    return {
                        "success": True,
                        "total_sales": 0.0,
                        "voucher_count": 0,
                        "party_name": party_name,
                        "from_date": from_date,
                        "to_date": to_date
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get sales: {str(e)}")
            return {"success": False, "message": f"Failed to get sales: {str(e)}"}
    
    async def get_database_info(self, database_name: str) -> Dict:
        """Get information about the database and its tables."""
        try:
            # Get list of tables
            tables_query = """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'mst_%' OR table_name LIKE 'trn_%'
            ORDER BY table_name
            """
            
            result = await self.execute_query(database_name, tables_query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "database_name": database_name,
                    "tables": result.get("data", []),
                    "table_count": result.get("count", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get database info: {str(e)}")
            return {"success": False, "message": f"Failed to get database info: {str(e)}"}
    
    async def validate_database_access(self, database_name: str) -> Dict:
        """Validate that the database exists and is accessible."""
        try:
            # Test basic connectivity
            connection_test = await self.test_connection(database_name)
            if not connection_test.get("success"):
                return connection_test
            
            # Test table access
            info_result = await self.get_database_info(database_name)
            if not info_result.get("success"):
                return info_result
            
            # Check if required tables exist
            required_tables = ['mst_ledger', 'trn_voucher', 'trn_accounting']
            existing_tables = [table['table_name'] for table in info_result.get('tables', [])]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                return {
                    "success": False,
                    "message": f"Required tables missing: {', '.join(missing_tables)}"
                }
            
            return {
                "success": True,
                "message": "Database access validated",
                "table_count": info_result.get("table_count", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Database validation failed: {str(e)}")
            return {"success": False, "message": f"Database validation failed: {str(e)}"}


# Global SQL service instance
tally_sql_service = TallySQLService()
