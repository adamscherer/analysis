# Stocks Project

## Supabase Setup and Management

### Initial Setup
1. Install the Supabase CLI:
   ```bash
   brew install supabase/tap/supabase
   ```

2. Create a `.env` file in the project root with your Supabase credentials:
   ```
   SUPABASE_URL=your-project-url
   SUPABASE_KEY=your-anon-key
   ```

3. Link your local project to your Supabase project:
   ```bash
   supabase link --project-ref your-project-ref
   ```

### Database Migrations

#### Creating Migrations
1. Create a new migration:
   ```bash
   supabase migration new migration_name
   ```
   This will create a new file in `supabase/migrations/` with a timestamp prefix.

2. Write your SQL schema changes in the migration file. Example:
   ```sql
   -- Create stocks table
   CREATE TABLE IF NOT EXISTS stocks (
       id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
       symbol TEXT NOT NULL,
       exchange TEXT NOT NULL,
       security_name TEXT NOT NULL,
       market_category TEXT,
       test_issue BOOLEAN DEFAULT FALSE,
       financial_status TEXT,
       round_lot_size INTEGER DEFAULT 100,
       etf BOOLEAN DEFAULT FALSE,
       next_shares BOOLEAN DEFAULT FALSE,
       cqs_symbol TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
   );

   -- Create an index for faster lookups by symbol
   CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);
   ```

#### Applying Migrations
1. Push migrations to your Supabase project:
   ```bash
   supabase db push
   ```

2. To reset your database and apply all migrations:
   ```bash
   supabase db reset
   ```

### Local Development
1. Start a local Supabase instance:
   ```bash
   supabase start
   ```

2. Stop the local instance:
   ```bash
   supabase stop
   ```

### Best Practices
- Keep migrations small and focused
- Include both `up` and `down` migrations when possible
- Test migrations locally before pushing to production
- Use meaningful migration names
- Document schema changes in commit messages
- Consider using `IF NOT EXISTS` for table creation
- Always include `created_at` and `updated_at` timestamps
- Add indexes for frequently queried columns

### Project Structure
```
supabase/
├── migrations/     # Database migrations
└── sql/           # SQL scripts and functions
```

### Useful Commands
- View migration status: `supabase migration list`
- Generate types: `supabase gen types typescript --local > types/supabase.ts`
- Pull remote schema: `supabase db pull`
