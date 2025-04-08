create table "public"."stocks" (
    "id" text not null,
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
    "created_at" timestamp with time zone not null default timezone('utc'::text, now()),
    "updated_at" timestamp with time zone not null default timezone('utc'::text, now())
);


CREATE INDEX idx_stocks_symbol ON public.stocks USING btree (symbol);

CREATE UNIQUE INDEX stocks_pkey ON public.stocks USING btree (id);

CREATE UNIQUE INDEX unique_symbol_exchange ON public.stocks USING btree (symbol, exchange);

alter table "public"."stocks" add constraint "stocks_pkey" PRIMARY KEY using index "stocks_pkey";

alter table "public"."stocks" add constraint "unique_symbol_exchange" UNIQUE using index "unique_symbol_exchange";

grant delete on table "public"."stocks" to "anon";

grant insert on table "public"."stocks" to "anon";

grant references on table "public"."stocks" to "anon";

grant select on table "public"."stocks" to "anon";

grant trigger on table "public"."stocks" to "anon";

grant truncate on table "public"."stocks" to "anon";

grant update on table "public"."stocks" to "anon";

grant delete on table "public"."stocks" to "authenticated";

grant insert on table "public"."stocks" to "authenticated";

grant references on table "public"."stocks" to "authenticated";

grant select on table "public"."stocks" to "authenticated";

grant trigger on table "public"."stocks" to "authenticated";

grant truncate on table "public"."stocks" to "authenticated";

grant update on table "public"."stocks" to "authenticated";

grant delete on table "public"."stocks" to "service_role";

grant insert on table "public"."stocks" to "service_role";

grant references on table "public"."stocks" to "service_role";

grant select on table "public"."stocks" to "service_role";

grant trigger on table "public"."stocks" to "service_role";

grant truncate on table "public"."stocks" to "service_role";

grant update on table "public"."stocks" to "service_role";


