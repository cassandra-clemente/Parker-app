-- Step 1: Create the trigger function
CREATE OR REPLACE FUNCTION update_block_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE blocks
    SET last_updated = NEW.reported_at
    WHERE id = NEW.block_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Attach the trigger to status_reports
CREATE TRIGGER trigger_update_block_timestamp
AFTER INSERT ON status_reports
FOR EACH ROW
EXECUTE FUNCTION update_block_last_updated();

SELECT COUNT(*) FROM public.block_restrictions;

UPDATE public.blocks
SET status = 'unknown';
