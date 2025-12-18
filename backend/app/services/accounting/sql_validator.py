# app/services/accounting/sql_validator.py

import sqlparse
import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("ProjectAria.SQLValidator")


class SQLValidator:
    """Validates SQL queries to ensure read-only access only."""
    
    # Allowed SQL keywords for read-only operations
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'FULL', 'OUTER',
        'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'FULL JOIN', 'OUTER JOIN',
        'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE', 'IS', 'IS NOT',
        'NULL', 'NOT NULL', 'TRUE', 'FALSE', 'ORDER', 'BY', 'ORDER BY', 'GROUP', 'GROUP BY', 'HAVING', 'DISTINCT', 'AS', 'ASC', 'DESC',
        'LIMIT', 'OFFSET', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'COALESCE', 'NULLIF',
        'SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE', 'ROUND', 'TRUNC',
        'UPPER', 'LOWER', 'LENGTH', 'SUBSTRING', 'CONCAT', 'REPLACE', 'TRIM',
        'CAST', 'EXTRACT', 'DATE_PART', 'NOW', 'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP',
        'UNION', 'INTERSECT', 'EXCEPT'
    }
    
    # Forbidden keywords that could modify data
    FORBIDDEN_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL', 'BEGIN', 'COMMIT', 'ROLLBACK',
        'SAVEPOINT', 'RELEASE', 'LOCK', 'UNLOCK', 'ANALYZE', 'VACUUM', 'REINDEX',
        'COPY', 'LOAD', 'IMPORT', 'EXPORT', 'BACKUP', 'RESTORE', 'SHUTDOWN', 'RESTART'
    }
    
    # Forbidden function patterns
    FORBIDDEN_FUNCTIONS = {
        'pg_', 'system_', 'admin_', 'superuser_', 'backup_', 'restore_',
        'exec', 'execute', 'eval', 'system', 'shell', 'cmd'
    }
    
    def __init__(self):
        self.allowed_tables = self._get_allowed_tables()
    
    def _get_allowed_tables(self) -> set:
        """Get list of allowed table names from Tally structure."""
        # These are the standard Tally table prefixes
        return {
            'mst_', 'trn_', 'tally_', 'company_', 'ledger_', 'voucher_',
            'stock_', 'item_', 'party_', 'group_', 'category_', 'centre_',
            'batch_', 'bank_', 'bill_', 'employee_', 'attendance_', 'payhead_'
        }
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for read-only access.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic input validation
            if not query or not query.strip():
                return False, "Empty query provided"
            
            # Clean and normalize the query
            cleaned_query = self._clean_query(query)
            
            # Parse the SQL
            parsed = sqlparse.parse(cleaned_query)
            if not parsed:
                return False, "Invalid SQL syntax"
            
            # Validate each statement
            for statement in parsed:
                if not self._validate_statement(statement):
                    forbidden_ops = self._get_forbidden_operations(statement)
                    if forbidden_ops:
                        return False, f"Query contains forbidden operations: {forbidden_ops}"
                    else:
                        return False, "Query validation failed - invalid statement structure"
            
            # Additional security checks
            security_issues = self._check_security_patterns(cleaned_query)
            if security_issues:
                return False, f"Security violation detected: {', '.join(security_issues)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"SQL validation error: {str(e)}")
            return False, f"Query validation failed: {str(e)}"
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the SQL query."""
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        return query
    
    def _validate_statement(self, statement) -> bool:
        """Validate a single SQL statement."""
        # Get the first token to determine statement type
        first_token = statement.token_first(skip_ws=True, skip_cm=True)
        if not first_token:
            return False
        
        statement_type = first_token.ttype
        statement_value = first_token.value.upper()
        
        # Check if it's a SELECT statement
        if (statement_type is sqlparse.tokens.Keyword or 
            statement_type is sqlparse.tokens.Keyword.DML) and statement_value == 'SELECT':
            return self._validate_select_statement(statement)
        
        # Only SELECT statements are allowed
        return False
    
    def _validate_select_statement(self, statement) -> bool:
        """Validate SELECT statement components."""
        tokens = list(statement.flatten())
        
        for token in tokens:
            if (token.ttype is sqlparse.tokens.Keyword or 
                token.ttype is sqlparse.tokens.Keyword.DML or
                token.ttype is sqlparse.tokens.Keyword.DDL):
                keyword = token.value.upper()
                
                # Check for forbidden keywords
                if keyword in self.FORBIDDEN_KEYWORDS:
                    return False
                
                # Check for allowed keywords
                if keyword not in self.ALLOWED_KEYWORDS:
                    # Allow some flexibility for table/column names
                    if not self._is_identifier(keyword):
                        return False
        
        return True
    
    def _is_identifier(self, value: str) -> bool:
        """Check if a value is likely an identifier (table/column name)."""
        # Allow alphanumeric identifiers with underscores
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value))
    
    def _check_security_patterns(self, query: str) -> List[str]:
        """Check for security violation patterns."""
        issues = []
        query_lower = query.lower()
        
        # Check for forbidden function patterns
        for pattern in self.FORBIDDEN_FUNCTIONS:
            if pattern in query_lower:
                issues.append(f"Forbidden function pattern: {pattern}")
        
        # Check for SQL injection patterns
        injection_patterns = [
            r'union\s+select', r';\s*drop', r';\s*delete', r';\s*insert',
            r';\s*update', r';\s*create', r';\s*alter', r';\s*exec',
            r'xp_cmdshell', r'sp_executesql', r'load_file', r'into\s+outfile'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_lower):
                issues.append(f"Potential SQL injection pattern: {pattern}")
        
        # Check for system table access
        system_tables = ['pg_', 'information_schema', 'sys', 'mysql', 'performance_schema']
        for table in system_tables:
            if table in query_lower:
                issues.append(f"System table access detected: {table}")
        
        return issues
    
    def _get_forbidden_operations(self, statement) -> List[str]:
        """Get list of forbidden operations found in statement."""
        forbidden = []
        tokens = list(statement.flatten())
        
        for token in tokens:
            if token.ttype is sqlparse.tokens.Keyword:
                keyword = token.value.upper()
                if keyword in self.FORBIDDEN_KEYWORDS:
                    forbidden.append(keyword)
        
        return forbidden
    
    def validate_table_access(self, query: str, allowed_tables: List[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate that query only accesses allowed tables.
        
        Args:
            query: SQL query to validate
            allowed_tables: List of allowed table names (optional)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not allowed_tables:
            allowed_tables = []
        
        # Extract table names from query
        table_names = self._extract_table_names(query)
        
        for table in table_names:
            # Check if table is in allowed list
            if allowed_tables and table not in allowed_tables:
                return False, f"Access to table '{table}' is not allowed"
            
            # Check if table matches allowed patterns
            if not any(table.startswith(prefix) for prefix in self.allowed_tables):
                return False, f"Table '{table}' does not match allowed patterns"
        
        return True, None
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query."""
        table_names = []
        
        # Simple and reliable approach: find table names after FROM and JOIN
        # Split query into lines and process each line
        lines = query.split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith('FROM ') or line.upper().startswith('JOIN '):
                # Extract table name from this line
                parts = line.split()
                if len(parts) >= 2:
                    table_name = parts[1]
                    # Remove schema prefix if present
                    table_name = table_name.split('.')[-1]
                    # Remove any trailing characters like commas, WHERE, etc.
                    table_name = table_name.split(',')[0].split('WHERE')[0].split('GROUP')[0].split('ORDER')[0].strip()
                    # Only add if it looks like a valid table name
                    if (table_name and 
                        table_name.replace('_', '').isalnum() and 
                        not any(char in table_name for char in ['(', ')', "'", '"'])):
                        table_names.append(table_name)
        
        return table_names
    
    def get_query_info(self, query: str) -> dict:
        """
        Get information about the query for logging/debugging.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Dictionary with query information
        """
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                return {"error": "Could not parse query"}
            
            statement = parsed[0]
            tokens = list(statement.flatten())
            
            # Extract basic information
            keywords = [token.value.upper() for token in tokens if token.ttype is sqlparse.tokens.Keyword]
            table_names = self._extract_table_names(query)
            
            return {
                "statement_type": keywords[0] if keywords else "UNKNOWN",
                "keywords": keywords,
                "table_names": table_names,
                "query_length": len(query),
                "is_read_only": self.validate_query(query)[0]
            }
            
        except Exception as e:
            return {"error": str(e)}


# Global validator instance
sql_validator = SQLValidator()
