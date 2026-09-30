// ============================================================
// 1. ALL SUPPLY CHAIN NODES
// ============================================================

MATCH (n)
RETURN n;


// ============================================================
// 2. ALL RELATIONSHIPS
// ============================================================

MATCH (a)-[r]->(b)
RETURN a, r, b;


// ============================================================
// 3. EVENT → SUPPLIER → PRODUCT
// ============================================================

MATCH (e:Event)-[:AFFECTS]->(s:Supplier)-[:SUPPLIES]->(p:Product)
RETURN e, s, p;


// ============================================================
// 4. COMPLETE GRAPH AROUND AN EVENT
// ============================================================

MATCH path =
    (e:Event {event_id: $event_id})-[*1..4]-(connected)
RETURN path;


// ============================================================
// 5. DIRECTLY AFFECTED SUPPLIERS
// ============================================================

MATCH (e:Event {event_id: $event_id})
      -[:AFFECTS]->(s:Supplier)

RETURN s;


// ============================================================
// 6. PRODUCTS AFFECTED BY AN EVENT
// ============================================================

MATCH (e:Event {event_id: $event_id})
      -[:AFFECTS]->(s:Supplier)
      -[:SUPPLIES]->(p:Product)

RETURN DISTINCT p;


// ============================================================
// 7. DOWNSTREAM RIPPLE PATH
// ============================================================

MATCH path =
    (e:Event {event_id: $event_id})
    -[*1..5]->
    (downstream)

RETURN path;


// ============================================================
// 8. GRAPH STATISTICS
// ============================================================

MATCH (n)
WITH count(n) AS total_nodes

MATCH ()-[r]->()
RETURN
    total_nodes,
    count(r) AS total_relationships;