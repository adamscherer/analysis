create table "stocks" (
  "cik" char(10) primary key,
  "symbol" text not null,
  "security_name" text not null,
  "entity_type" text,
  "sic" text,
  "sic_description" text,
  "owner_org" text,
  "insider_transaction_for_owner_exists" integer,
  "insider_transaction_for_issuer_exists" integer,
  "tickers" text[],
  "exchanges" text[],
  "ein" text,
  "lei" text,
  "description" text,
  "website" text,
  "investor_website" text,
  "category" text,
  "fiscal_year_end" text,
  "state_of_incorporation" text,
  "state_of_incorporation_description" text,
  "addresses" jsonb,
  "phone" text,
  "flags" text,
  "former_names" jsonb[],
  "basic_shares" numeric,
  "diluted_shares" numeric,
  "dilution_percentage" numeric,
  "created_at" timestamp with time zone default timezone('utc'::text, now()) not null,
  "updated_at" timestamp with time zone default timezone('utc'::text, now()) not null
);

create index if not exists idx_stocks_symbol on stocks(symbol);
create index if not exists idx_stocks_sic on stocks(sic);
create index if not exists idx_stocks_entity_type on stocks(entity_type);