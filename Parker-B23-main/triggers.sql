---- Step 1: Create the trigger function
CREATE OR REPLACE FUNCTION update_block_status_from_report()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE blocks
    SET status = NEW.status,
        last_updated = NOW()
    WHERE id = NEW.block_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger on status_reports
CREATE TRIGGER trigger_update_block_status
AFTER INSERT ON status_reports
FOR EACH ROW
EXECUTE FUNCTION update_block_status_from_report();




--Credit Update trigger function
CREATE OR REPLACE FUNCTION apply_credit_transaction()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.reason = 'deposit' THEN
        UPDATE public.users
        SET credits = credits + NEW.amount
        WHERE id = NEW.user_id;

    ELSIF NEW.reason = 'withdrawal' THEN
        UPDATE public.users
        SET credits = credits - NEW.amount
        WHERE id = NEW.user_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

--Create trigger

CREATE TRIGGER trigger_apply_credit_transaction
AFTER INSERT ON public.credit_transactions
FOR EACH ROW
EXECUTE FUNCTION apply_credit_transaction();


