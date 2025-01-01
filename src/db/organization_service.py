from sqlalchemy import text

class OrganizationService:
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def get_organization_info(self, organization_id: str) -> str:
        """
        Retrieves and formats information about programs and locations for a given organization.

        Args:
            organization_id: The UUID of the organization.

        Returns:
            A formatted string containing program names and IDs, and location names and IDs.
        """
        programs_info = []
        locations_info = []

        with self.db_engine.connect() as connection:
            # Fetch programs
            programs_query = text(
                "SELECT id, name FROM programs WHERE location_id IN "
                "(SELECT id FROM locations WHERE organization_id = :org_id)"
            )
            programs_result = connection.execute(programs_query, {"org_id": organization_id}).fetchall()
            for row in programs_result:
                programs_info.append(f"- {row.name} (ID: {row.id})")

            # Fetch locations
            locations_query = text(
                "SELECT id, short_name FROM locations WHERE organization_id = :org_id"
            )
            locations_result = connection.execute(locations_query, {"org_id": organization_id}).fetchall()
            for row in locations_result:
                locations_info.append(f"- {row.short_name} (ID: {row.id})")

        return "Programs:\n" + "\n".join(programs_info) + "\n\nLocations:\n" + "\n".join(locations_info) 