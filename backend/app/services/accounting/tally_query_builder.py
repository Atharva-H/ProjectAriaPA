# app/services/accounting/tally_query_builder.py

import yaml
from typing import Dict, List, Optional, Any
import logging
from .sql_validator import sql_validator

logger = logging.getLogger("ProjectAria.TallyQueryBuilder")


class TallyQueryBuilder:
    """Builds SQL queries from Tally structure definitions."""
    
    def __init__(self, structure_file: str = None):
        """Initialize with YAML structure file."""
        self.structure_file = structure_file or "/Users/atharvahumar/Documents/Projects/ProjectAriaPA/backend/app/services/accounting/tally_structure.yaml"
        self.structure = self._load_structure()
        self.table_mappings = self._build_table_mappings()
        self.relationships = self._build_relationships()
    
    def _load_structure(self) -> Dict:
        """Load Tally structure from YAML file."""
        try:
            with open(self.structure_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load structure file: {str(e)}")
            return {}
    
    def _build_table_mappings(self) -> Dict[str, str]:
        """Build mapping from collection names to table names."""
        mappings = {}
        
        # Master tables
        if 'master' in self.structure:
            for table in self.structure['master']:
                name = table.get('name', '')
                if name:
                    mappings[name] = name  # Table names are the same as collection names
        
        # Transaction tables
        if 'transaction' in self.structure:
            for table in self.structure['transaction']:
                name = table.get('name', '')
                if name:
                    mappings[name] = name
        
        return mappings
    
    def _build_relationships(self) -> Dict[str, List[Dict]]:
        """Build relationship mappings from data_structure.md patterns."""
        # Based on the relationships defined in data_structure.md
        relationships = {
            'mst_ledger': [
                {'table': 'trn_accounting', 'field': 'ledger', 'type': 'one_to_many'},
                {'table': 'trn_cost_centre', 'field': 'ledger', 'type': 'one_to_many'},
                {'table': 'trn_bill', 'field': 'ledger', 'type': 'one_to_many'},
                {'table': 'trn_bank', 'field': 'ledger', 'type': 'one_to_many'}
            ],
            'trn_voucher': [
                {'table': 'trn_accounting', 'field': 'guid', 'type': 'one_to_many'},
                {'table': 'trn_inventory', 'field': 'guid', 'type': 'one_to_many'},
                {'table': 'trn_cost_centre', 'field': 'guid', 'type': 'one_to_many'},
                {'table': 'trn_bill', 'field': 'guid', 'type': 'one_to_many'},
                {'table': 'trn_bank', 'field': 'guid', 'type': 'one_to_many'},
                {'table': 'trn_batch', 'field': 'guid', 'type': 'one_to_many'}
            ],
            'mst_stock_item': [
                {'table': 'trn_inventory', 'field': 'item', 'type': 'one_to_many'},
                {'table': 'trn_batch', 'field': 'item', 'type': 'one_to_many'}
            ],
            'mst_godown': [
                {'table': 'trn_inventory', 'field': 'godown', 'type': 'one_to_many'},
                {'table': 'trn_batch', 'field': 'godown', 'type': 'one_to_many'}
            ]
        }
        return relationships
    
    def build_ledgers_query(self, filters: Dict = None) -> str:
        """Build SQL query for ledgers with pagination."""
        query = """
        SELECT 
            name,
            parent,
            opening_balance,
            closing_balance,
            is_revenue,
            is_deemedpositive,
            mailing_name,
            email,
            gstn
        FROM mst_ledger
        WHERE name IS NOT NULL
        """
        
        if filters:
            if filters.get('parent'):
                query += f" AND parent = '{filters['parent']}'"
            if filters.get('is_revenue') is not None:
                query += f" AND is_revenue = {filters['is_revenue']}"
        
        query += " ORDER BY name"
        
        # Add pagination
        if filters and filters.get('limit'):
            query += f" LIMIT {filters['limit']}"
            if filters.get('offset'):
                query += f" OFFSET {filters['offset']}"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_vouchers_query(self, filters: Dict = None) -> str:
        """Build SQL query for vouchers with accounting filter and pagination."""
        query = """
        SELECT 
            v.date,
            v.voucher_type,
            v.voucher_number,
            v.party_name,
            v.narration,
            v.is_invoice,
            v.is_accounting_voucher,
            v.is_inventory_voucher,
            v.is_order_voucher,
            a.ledger,
            a.amount
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE v.is_order_voucher = 0
        """
        
        if filters:
            if filters.get('from_date'):
                query += f" AND v.date >= '{filters['from_date']}'"
            if filters.get('to_date'):
                query += f" AND v.date <= '{filters['to_date']}'"
            if filters.get('voucher_type'):
                query += f" AND v.voucher_type = '{filters['voucher_type']}'"
            if filters.get('is_invoice') is not None:
                query += f" AND v.is_invoice = {filters['is_invoice']}"
            if filters.get('accounting_only', True):
                query += " AND v.is_inventory_voucher = 0"
        
        query += " ORDER BY v.date DESC"
        
        # Add pagination
        if filters and filters.get('limit'):
            query += f" LIMIT {filters['limit']}"
            if filters.get('offset'):
                query += f" OFFSET {filters['offset']}"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_ledger_balance_query(self, ledger_name: str = None, as_of_date: str = None) -> str:
        """Build SQL query for ledger balance calculation."""
        query = """
        SELECT 
            l.name,
            l.opening_balance,
            SUM(CASE WHEN a.amount < 0 THEN -a.amount ELSE 0 END) AS net_debit,
            SUM(CASE WHEN a.amount > 0 THEN a.amount ELSE 0 END) AS net_credit,
            (l.opening_balance + SUM(COALESCE(a.amount, 0))) AS closing_balance
        FROM mst_ledger l
        LEFT JOIN trn_accounting a ON l.name = a.ledger
        LEFT JOIN trn_voucher v ON a.guid = v.guid
        WHERE (v.is_order_voucher = 0 OR v.is_order_voucher IS NULL)
          AND (v.is_inventory_voucher = 0 OR v.is_inventory_voucher IS NULL)
        """
        
        if ledger_name:
            query += f" AND l.name = '{ledger_name}'"
        
        if as_of_date:
            query += f" AND (v.date IS NULL OR v.date <= '{as_of_date}')"
        
        query += """
        GROUP BY l.name, l.opening_balance
        ORDER BY l.name
        """
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_stock_items_query(self, filters: Dict = None) -> str:
        """Build SQL query for stock items."""
        query = """
        SELECT 
            name,
            parent,
            uom,
            opening_balance,
            opening_rate,
            opening_value,
            closing_balance,
            closing_rate,
            closing_value,
            costing_method,
            gst_hsn_code,
            gst_rate
        FROM mst_stock_item
        WHERE name IS NOT NULL
        """
        
        if filters:
            if filters.get('parent'):
                query += f" AND parent = '{filters['parent']}'"
            if filters.get('uom'):
                query += f" AND uom = '{filters['uom']}'"
        
        query += " ORDER BY name"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_parties_query(self, filters: Dict = None) -> str:
        """Build SQL query for parties (debtors/creditors)."""
        query = """
        SELECT 
            name,
            parent,
            opening_balance,
            closing_balance,
            mailing_name,
            mailing_address,
            email,
            gstn,
            bank_account_number
        FROM mst_ledger
        WHERE (parent LIKE '%Sundry Debtors%' OR parent LIKE '%Sundry Creditors%')
          AND name IS NOT NULL
        """
        
        if filters:
            if filters.get('parent_type') == 'debtors':
                query += " AND parent LIKE '%Sundry Debtors%'"
            elif filters.get('parent_type') == 'creditors':
                query += " AND parent LIKE '%Sundry Creditors%'"
        
        query += " ORDER BY name"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_sales_query(self, party_name: str = None, from_date: str = None, to_date: str = None) -> str:
        """Build SQL query for calculating sales for a specific party within a date range."""
        # List of sales voucher types (based on user's SQL query)
        sales_types = [
            "Sales", "Sales 25-26", "Sales by Amazon", "Sales by Amazon (FBA Khandwa)",
            "Sales by Amazon (From Paricott Godown)", "Sales by Flipkart", "Sales by Just Dial",
            "Sales Cust.", "Sales Export", "Sales Jio Mart", "Sales MT"
        ]
        
        # Build the WHERE clause for voucher types
        sales_types_condition = " OR ".join([f"v.voucher_type = '{t}'" for t in sales_types])
        
        query = """
        SELECT 
            SUM(ABS(a.amount)) AS total_sales,
            COUNT(DISTINCT v.guid) AS voucher_count
        FROM trn_voucher v
        LEFT JOIN trn_accounting a ON v.guid = a.guid
        WHERE v.is_order_voucher = 0
          AND v.is_inventory_voucher = 0
          AND (v.is_accounting_voucher = 1 OR v.is_accounting_voucher IS NULL)
          AND a.amount < 0
          AND ({})
        """.format(sales_types_condition)
        
        if party_name:
            query += f" AND v.party_name = '{party_name}' AND a.ledger = '{party_name}'"
        
        if from_date:
            query += f" AND v.date >= '{from_date}'"
        
        if to_date:
            query += f" AND v.date <= '{to_date}'"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_inventory_query(self, filters: Dict = None) -> str:
        """Build SQL query for inventory transactions."""
        query = """
        SELECT 
            v.date,
            v.voucher_type,
            v.voucher_number,
            i.item,
            i.quantity,
            i.rate,
            i.amount,
            i.godown,
            i.tracking_number
        FROM trn_voucher v
        JOIN trn_inventory i ON v.guid = i.guid
        WHERE v.is_order_voucher = 0
        """
        
        if filters:
            if filters.get('from_date'):
                query += f" AND v.date >= '{filters['from_date']}'"
            if filters.get('to_date'):
                query += f" AND v.date <= '{filters['to_date']}'"
            if filters.get('item'):
                query += f" AND i.item = '{filters['item']}'"
            if filters.get('godown'):
                query += f" AND i.godown = '{filters['godown']}'"
            if filters.get('inventory_only', True):
                query += " AND v.is_inventory_voucher = 1"
        
        query += " ORDER BY v.date DESC"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_bill_tracking_query(self, filters: Dict = None) -> str:
        """Build SQL query for bill tracking (from data_structure.md)."""
        query = """
        WITH bill_data AS (
            SELECT 
                b.name,
                b.amount,
                b.billtype,
                v.date
            FROM trn_bill b
            JOIN trn_voucher v ON b.guid = v.guid
            WHERE v.is_order_voucher = 0 
              AND v.is_inventory_voucher = 0
              AND b.billtype != 'On Account'
        )
        SELECT
            lt.name AS bill_name,
            lt.amount AS bill_amount,
            COALESCE(rt.adjusted_amount, 0) AS adjusted_amount,
            (lt.amount + COALESCE(rt.adjusted_amount, 0)) AS pending_amount
        FROM (
            SELECT name, amount
            FROM bill_data
            WHERE billtype IN ('New Ref', 'Advance')
        ) AS lt
        LEFT JOIN (
            SELECT name, SUM(amount) AS adjusted_amount
            FROM bill_data
            WHERE billtype = 'Agst Ref'
            GROUP BY name
        ) AS rt ON lt.name = rt.name
        """
        
        if filters:
            if filters.get('bill_name'):
                query += f" AND lt.name = '{filters['bill_name']}'"
            if filters.get('pending_only'):
                query += " HAVING (lt.amount + COALESCE(rt.adjusted_amount, 0)) > 0"
        
        query += " ORDER BY lt.name"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def build_custom_query(self, base_table: str, fields: List[str], 
                          joins: List[Dict] = None, filters: Dict = None,
                          order_by: str = None, limit: int = None) -> str:
        """
        Build a custom SQL query with specified parameters.
        
        Args:
            base_table: Primary table name
            fields: List of fields to select
            joins: List of join specifications
            filters: Dictionary of filter conditions
            order_by: ORDER BY clause
            limit: LIMIT clause
            
        Returns:
            SQL query string
        """
        # Start with SELECT and fields
        query = f"SELECT {', '.join(fields)} FROM {base_table}"
        
        # Add joins
        if joins:
            for join in joins:
                join_type = join.get('type', 'JOIN')
                table = join.get('table')
                condition = join.get('condition')
                if table and condition:
                    query += f" {join_type} {table} ON {condition}"
        
        # Add WHERE clause
        if filters:
            where_conditions = []
            for field, value in filters.items():
                if isinstance(value, str):
                    where_conditions.append(f"{field} = '{value}'")
                else:
                    where_conditions.append(f"{field} = {value}")
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT
        if limit:
            query += f" LIMIT {limit}"
        
        # Validate the query
        is_valid, error = sql_validator.validate_query(query)
        if not is_valid:
            raise ValueError(f"Invalid query generated: {error}")
        
        return query
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get information about a table from the structure."""
        # Search in master tables
        if 'master' in self.structure:
            for table in self.structure['master']:
                if table.get('name') == table_name:
                    return {
                        'name': table.get('name'),
                        'collection': table.get('collection'),
                        'nature': table.get('nature'),
                        'fields': table.get('fields', [])
                    }
        
        # Search in transaction tables
        if 'transaction' in self.structure:
            for table in self.structure['transaction']:
                if table.get('name') == table_name:
                    return {
                        'name': table.get('name'),
                        'collection': table.get('collection'),
                        'nature': table.get('nature'),
                        'fields': table.get('fields', [])
                    }
        
        return {}


# Global query builder instance
tally_query_builder = TallyQueryBuilder()
