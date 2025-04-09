create table "public"."stocks" (
    "cik" character(10) not null,
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
    "created_at" timestamp with time zone not null default timezone('utc'::text, now()),
    "updated_at" timestamp with time zone not null default timezone('utc'::text, now())
);


CREATE INDEX idx_stocks_entity_type ON public.stocks USING btree (entity_type);

CREATE INDEX idx_stocks_sic ON public.stocks USING btree (sic);

CREATE INDEX idx_stocks_symbol ON public.stocks USING btree (symbol);

CREATE UNIQUE INDEX stocks_pkey ON public.stocks USING btree (cik);

alter table "public"."stocks" add constraint "stocks_pkey" PRIMARY KEY using index "stocks_pkey";

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


