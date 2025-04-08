create table "stocks" (
  "id" text primary key,
  "symbol" text not null,
  "security_name" text not null,
  "exchange" text not null,
  "market_category" text,
  "test_issue" boolean default false,
  "financial_status" text,
  "round_lot_size" integer default 100,
  "etf" boolean default false,
  "next_shares" boolean default false,
  "cqs_symbol" text,
  "created_at" timestamp with time zone default timezone('utc'::text, now()) not null,
  "updated_at" timestamp with time zone default timezone('utc'::text, now()) not null,
);

create index if not exists idx_stocks_symbol on stocks(symbol);