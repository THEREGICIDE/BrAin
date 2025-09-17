"""
BigQuery Database Service with Comprehensive Logging
"""
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
from app.config import settings

logger = structlog.get_logger(__name__)

class BigQueryService:
    """Service for all BigQuery operations with detailed logging"""
    
    def __init__(self):
        logger.info("Initializing BigQuery service",
                   project=settings.google_cloud_project,
                   dataset=settings.bigquery_dataset)
        
        self.client = bigquery.Client(project=settings.google_cloud_project)
        self.dataset_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
        
        # Initialize dataset and tables
        self._initialize_dataset()
        self._initialize_tables()
        
        logger.info("BigQuery service initialized successfully")
    
    def _initialize_dataset(self):
        """Create dataset if it doesn't exist"""
        try:
            dataset = bigquery.Dataset(self.dataset_id)
            dataset.location = settings.bigquery_location
            dataset.description = "AI Trip Planner Application Data"
            
            try:
                self.client.get_dataset(self.dataset_id)
                logger.info(f"Dataset {self.dataset_id} already exists")
            except NotFound:
                dataset = self.client.create_dataset(dataset, timeout=30)
                logger.info(f"Created dataset {self.dataset_id}",
                           location=dataset.location)
                
        except Exception as e:
            logger.error(f"Error initializing dataset: {str(e)}",
                        dataset_id=self.dataset_id)
            raise
    
    def _initialize_tables(self):
        """Create required tables if they don't exist"""
        tables_schema = {
            settings.bigquery_table_trips: [
                bigquery.SchemaField("trip_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("destination", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("start_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("end_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("duration_days", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("total_budget", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("actual_cost", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("travelers_count", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("themes", "STRING", mode="REPEATED"),
                bigquery.SchemaField("itinerary_data", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("booking_status", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("payment_status", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
            ],
            settings.bigquery_table_users: [
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("full_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("phone_number", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("preferences", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("travel_history", "STRING", mode="REPEATED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
            ],
            settings.bigquery_table_bookings: [
                bigquery.SchemaField("booking_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("trip_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("booking_items", "JSON", mode="REQUIRED"),
                bigquery.SchemaField("total_amount", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("currency", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("payment_method", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("payment_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("confirmed_at", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("cancelled_at", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("emt_reference", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
            ],
            settings.bigquery_table_analytics: [
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("session_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("event_data", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("ip_address", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
            ],
            settings.bigquery_table_logs: [
                bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("level", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("logger", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("message", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("context", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("error_trace", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("request_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
            ]
        }
        
        for table_name, schema in tables_schema.items():
            table_id = f"{self.dataset_id}.{table_name}"
            try:
                self.client.get_table(table_id)
                logger.info(f"Table {table_id} already exists")
            except NotFound:
                table = bigquery.Table(table_id, schema=schema)
                table = self.client.create_table(table)
                logger.info(f"Created table {table_id}",
                           num_fields=len(schema))
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {str(e)}")
    
    async def insert_trip(self, trip_data: Dict[str, Any]) -> str:
        """Insert a new trip into BigQuery"""
        try:
            logger.info("Inserting new trip into BigQuery",
                       destination=trip_data.get('destination'))
            
            trip_id = trip_data.get('trip_id', str(uuid.uuid4()))
            
            row = {
                "trip_id": trip_id,
                "user_id": trip_data.get('user_id'),
                "destination": trip_data['destination'],
                "start_date": trip_data['start_date'],
                "end_date": trip_data['end_date'],
                "duration_days": trip_data['duration_days'],
                "total_budget": trip_data['total_budget'],
                "actual_cost": trip_data.get('actual_cost'),
                "travelers_count": trip_data['travelers_count'],
                "themes": trip_data.get('themes', []),
                "itinerary_data": json.dumps(trip_data.get('itinerary_data', {})),
                "booking_status": trip_data.get('booking_status', 'draft'),
                "payment_status": trip_data.get('payment_status', 'pending'),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": json.dumps(trip_data.get('metadata', {}))
            }
            
            table_id = f"{self.dataset_id}.{settings.bigquery_table_trips}"
            errors = self.client.insert_rows_json(table_id, [row])
            
            if errors:
                logger.error("Failed to insert trip", errors=errors)
                raise Exception(f"Failed to insert trip: {errors}")
            
            logger.info("Trip inserted successfully",
                       trip_id=trip_id,
                       destination=trip_data['destination'])
            
            # Log analytics event
            await self.log_analytics_event("trip_created", {
                "trip_id": trip_id,
                "destination": trip_data['destination'],
                "budget": trip_data['total_budget']
            })
            
            return trip_id
            
        except Exception as e:
            logger.error(f"Error inserting trip: {str(e)}",
                        trip_data=trip_data)
            raise
    
    async def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve trip from BigQuery"""
        try:
            logger.info("Retrieving trip from BigQuery", trip_id=trip_id)
            
            query = f"""
                SELECT *
                FROM `{self.dataset_id}.{settings.bigquery_table_trips}`
                WHERE trip_id = @trip_id
                LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("trip_id", "STRING", trip_id)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                trip_data = dict(row)
                if trip_data.get('itinerary_data'):
                    trip_data['itinerary_data'] = json.loads(trip_data['itinerary_data'])
                if trip_data.get('metadata'):
                    trip_data['metadata'] = json.loads(trip_data['metadata'])
                
                logger.info("Trip retrieved successfully", trip_id=trip_id)
                return trip_data
            
            logger.warning("Trip not found", trip_id=trip_id)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving trip: {str(e)}", trip_id=trip_id)
            raise
    
    async def update_trip(self, trip_id: str, update_data: Dict[str, Any]) -> bool:
        """Update trip in BigQuery"""
        try:
            logger.info("Updating trip in BigQuery", trip_id=trip_id)
            
            # Build UPDATE statement dynamically
            set_clauses = []
            parameters = []
            
            for key, value in update_data.items():
                if key not in ['trip_id', 'created_at']:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    set_clauses.append(f"{key} = @{key}")
                    parameters.append(
                        bigquery.ScalarQueryParameter(key, "STRING" if isinstance(value, str) else "FLOAT", value)
                    )
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP()")
            
            query = f"""
                UPDATE `{self.dataset_id}.{settings.bigquery_table_trips}`
                SET {', '.join(set_clauses)}
                WHERE trip_id = @trip_id
            """
            
            parameters.append(bigquery.ScalarQueryParameter("trip_id", "STRING", trip_id))
            
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            logger.info("Trip updated successfully", trip_id=trip_id)
            return True
            
        except Exception as e:
            logger.error(f"Error updating trip: {str(e)}", trip_id=trip_id)
            raise
    
    async def insert_booking(self, booking_data: Dict[str, Any]) -> str:
        """Insert booking into BigQuery"""
        try:
            logger.info("Inserting booking into BigQuery",
                       trip_id=booking_data.get('trip_id'))
            
            booking_id = booking_data.get('booking_id', str(uuid.uuid4()))
            
            row = {
                "booking_id": booking_id,
                "trip_id": booking_data['trip_id'],
                "user_id": booking_data['user_id'],
                "booking_items": json.dumps(booking_data['booking_items']),
                "total_amount": booking_data['total_amount'],
                "currency": booking_data.get('currency', 'INR'),
                "status": booking_data.get('status', 'pending'),
                "payment_method": booking_data.get('payment_method'),
                "payment_id": booking_data.get('payment_id'),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "confirmed_at": booking_data.get('confirmed_at'),
                "cancelled_at": booking_data.get('cancelled_at'),
                "emt_reference": booking_data.get('emt_reference'),
                "metadata": json.dumps(booking_data.get('metadata', {}))
            }
            
            table_id = f"{self.dataset_id}.{settings.bigquery_table_bookings}"
            errors = self.client.insert_rows_json(table_id, [row])
            
            if errors:
                logger.error("Failed to insert booking", errors=errors)
                raise Exception(f"Failed to insert booking: {errors}")
            
            logger.info("Booking inserted successfully", booking_id=booking_id)
            
            # Log analytics event
            await self.log_analytics_event("booking_created", {
                "booking_id": booking_id,
                "trip_id": booking_data['trip_id'],
                "amount": booking_data['total_amount']
            })
            
            return booking_id
            
        except Exception as e:
            logger.error(f"Error inserting booking: {str(e)}")
            raise
    
    async def get_user_trips(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's trips from BigQuery"""
        try:
            logger.info("Retrieving user trips", user_id=user_id, limit=limit)
            
            query = f"""
                SELECT *
                FROM `{self.dataset_id}.{settings.bigquery_table_trips}`
                WHERE user_id = @user_id
                ORDER BY created_at DESC
                LIMIT @limit
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            trips = []
            for row in results:
                trip_data = dict(row)
                if trip_data.get('itinerary_data'):
                    trip_data['itinerary_data'] = json.loads(trip_data['itinerary_data'])
                trips.append(trip_data)
            
            logger.info(f"Retrieved {len(trips)} trips for user", user_id=user_id)
            return trips
            
        except Exception as e:
            logger.error(f"Error retrieving user trips: {str(e)}", user_id=user_id)
            raise
    
    async def log_analytics_event(self, event_type: str, event_data: Dict[str, Any],
                                 user_id: Optional[str] = None) -> None:
        """Log analytics event to BigQuery"""
        try:
            event_id = str(uuid.uuid4())
            
            row = {
                "event_id": event_id,
                "event_type": event_type,
                "user_id": user_id,
                "session_id": event_data.get('session_id'),
                "event_data": json.dumps(event_data),
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": event_data.get('ip_address'),
                "user_agent": event_data.get('user_agent'),
                "metadata": json.dumps(event_data.get('metadata', {}))
            }
            
            table_id = f"{self.dataset_id}.{settings.bigquery_table_analytics}"
            errors = self.client.insert_rows_json(table_id, [row])
            
            if errors:
                logger.error("Failed to log analytics event", errors=errors)
            else:
                logger.debug("Analytics event logged", event_type=event_type)
                
        except Exception as e:
            logger.error(f"Error logging analytics event: {str(e)}")
    
    async def log_application_log(self, log_entry: Dict[str, Any]) -> None:
        """Log application logs to BigQuery"""
        try:
            row = {
                "log_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "level": log_entry.get('level', 'INFO'),
                "logger": log_entry.get('logger', 'app'),
                "message": log_entry.get('message', ''),
                "context": json.dumps(log_entry.get('context', {})),
                "error_trace": log_entry.get('error_trace'),
                "request_id": log_entry.get('request_id'),
                "user_id": log_entry.get('user_id'),
                "metadata": json.dumps(log_entry.get('metadata', {}))
            }
            
            table_id = f"{self.dataset_id}.{settings.bigquery_table_logs}"
            errors = self.client.insert_rows_json(table_id, [row])
            
            if errors:
                logger.error("Failed to log to BigQuery", errors=errors)
                
        except Exception as e:
            logger.error(f"Error logging to BigQuery: {str(e)}")
    
    async def get_analytics_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get analytics summary from BigQuery"""
        try:
            logger.info("Getting analytics summary", 
                       start_date=start_date, end_date=end_date)
            
            query = f"""
                SELECT 
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_events,
                    event_type,
                    DATE(timestamp) as event_date
                FROM `{self.dataset_id}.{settings.bigquery_table_analytics}`
                WHERE DATE(timestamp) BETWEEN @start_date AND @end_date
                GROUP BY event_type, event_date
                ORDER BY event_date DESC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            analytics_data = []
            for row in results:
                analytics_data.append(dict(row))
            
            logger.info("Analytics summary retrieved", records=len(analytics_data))
            
            return {
                "period": f"{start_date} to {end_date}",
                "data": analytics_data
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {str(e)}")
            raise

# Initialize BigQuery service
bigquery_service = BigQueryService()