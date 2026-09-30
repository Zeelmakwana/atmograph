// ================================
// AtmoGraph Sample Supply Chain
// ================================

// Countries
MERGE (india:Country {id: "COUNTRY-IN"})
SET india.name = "India";

MERGE (netherlands:Country {id: "COUNTRY-NL"})
SET netherlands.name = "Netherlands";

MERGE (germany:Country {id: "COUNTRY-DE"})
SET germany.name = "Germany";


// Ports
MERGE (mumbai:Port {id: "PORT-MUMBAI"})
SET mumbai.name = "Mumbai Port";

MERGE (rotterdam:Port {id: "PORT-ROTTERDAM"})
SET rotterdam.name = "Rotterdam Port";


// Companies
MERGE (techsource:Company {id: "COMP-001"})
SET techsource.name = "TechSource Components";

MERGE (eurodevices:Company {id: "COMP-002"})
SET eurodevices.name = "EuroDevices GmbH";

MERGE (indiamobile:Company {id: "COMP-003"})
SET indiamobile.name = "IndiaMobile Electronics";


// Products
MERGE (chip:Product {id: "PROD-001"})
SET chip.name = "Mobile Processor";

MERGE (display:Product {id: "PROD-002"})
SET display.name = "OLED Display";

MERGE (smartphone:Product {id: "PROD-003"})
SET smartphone.name = "Smartphone";


// Country relationships
MERGE (techsource)-[:LOCATED_IN]->(india);
MERGE (eurodevices)-[:LOCATED_IN]->(germany);
MERGE (indiamobile)-[:LOCATED_IN]->(india);


// Port relationships
MERGE (techsource)-[:SHIPS_FROM]->(mumbai);
MERGE (eurodevices)-[:RECEIVES_AT]->(rotterdam);


// Supply relationships
MERGE (techsource)-[:SUPPLIES]->(chip);
MERGE (eurodevices)-[:SUPPLIES]->(display);

MERGE (indiamobile)-[:USES]->(chip);
MERGE (indiamobile)-[:USES]->(display);

MERGE (indiamobile)-[:PRODUCES]->(smartphone);


// Shipping relationships
MERGE (mumbai)-[:SHIPS_TO]->(rotterdam);


// Event
MERGE (event:Event {id: "EVENT-001"})
SET event.name = "Rotterdam Port Strike",
    event.type = "PORT_STRIKE",
    event.severity = 0.85;


// Event impact
MERGE (event)-[:AFFECTS]->(rotterdam);
MERGE (rotterdam)-[:RECEIVES_FROM]->(mumbai);