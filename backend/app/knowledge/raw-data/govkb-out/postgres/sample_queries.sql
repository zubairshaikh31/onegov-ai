-- =====================================================================
-- Sample AI-chatbot / search queries over the GovKB knowledge base
-- Assumes: CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- =====================================================================

-- 1. Find services by keyword (chatbot intent: "passport apply")
SELECT service_id, name, official_apply_link, helpline_number
FROM govkb.services
WHERE keywords::text ILIKE '%passport%'
   OR name ILIKE '%passport%'
ORDER BY name;

-- 2. Maharashtra state services only
SELECT service_id, name, official_portal
FROM govkb.services
WHERE government_level = 'State' AND state_id = 'MH'
ORDER BY name;

-- 3. Full Q&A for a service (render FAQ in chatbot)
SELECT q.question, q.answer
FROM govkb.faqs q
JOIN govkb.services s ON s.service_id = q.service_id
WHERE s.service_id = 'SVC-PMKISAN';

-- 4. Step-by-step for a service (guided flow)
SELECT step_order, description
FROM govkb.application_steps
WHERE service_id = 'SVC-AADHAAR'
ORDER BY step_order;

-- 5. Fuzzy search on service name (trgm)
SELECT service_id, name, ai_summary
FROM govkb.services
WHERE name % 'driving licance'   -- typo-tolerant
ORDER BY similarity(name, 'driving licance') DESC
LIMIT 5;

-- 6. Documents needed for a service
SELECT name, mandatory
FROM govkb.documents
WHERE service_id = 'SVC-GST'
ORDER BY mandatory DESC;

-- 7. Suggested follow-ups for a service (proactive bot prompts)
SELECT name, suggested_followups
FROM govkb.services
WHERE service_id = 'SVC-ITR';

-- 8. List all helplines (quick reference)
SELECT s.name, h.number, h.email
FROM govkb.helplines h
JOIN govkb.services s ON s.service_id = h.service_id
ORDER BY s.name;
