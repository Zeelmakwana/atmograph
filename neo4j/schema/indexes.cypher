CREATE INDEX event_name_index IF NOT EXISTS
FOR (e:Event)
ON (e.name);

CREATE INDEX company_name_index IF NOT EXISTS
FOR (c:Company)
ON (c.name);

CREATE INDEX product_name_index IF NOT EXISTS
FOR (p:Product)
ON (p.name);

CREATE INDEX port_name_index IF NOT EXISTS
FOR (p:Port)
ON (p.name);

CREATE INDEX country_name_index IF NOT EXISTS
FOR (c:Country)
ON (c.name);