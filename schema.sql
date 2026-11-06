BEGIN TRANSACTION;
CREATE TABLE audit_log(
              id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id),
              action TEXT NOT NULL, entity TEXT NOT NULL, entity_id INTEGER,
              detail TEXT NOT NULL, created_at TEXT NOT NULL
            );
CREATE TABLE cash_entries(
              id INTEGER PRIMARY KEY, shift_id INTEGER NOT NULL REFERENCES cash_shifts(id),
              kind TEXT NOT NULL CHECK(kind IN ('income','expense','refund')),
              amount INTEGER NOT NULL CHECK(amount > 0), method TEXT NOT NULL
                CHECK(method IN ('cash','bank')), note TEXT NOT NULL,
              reference TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id)
            );
CREATE TABLE cash_shifts(
              id INTEGER PRIMARY KEY, label TEXT NOT NULL, opened_at TEXT NOT NULL,
              opened_by INTEGER NOT NULL REFERENCES users(id),
              opening_cash INTEGER NOT NULL DEFAULT 0,
              manual_cash INTEGER NOT NULL DEFAULT 0, manual_bank INTEGER NOT NULL DEFAULT 0,
              counted_cash INTEGER, counted_bank INTEGER, note TEXT NOT NULL DEFAULT '',
              locked_at TEXT, locked_by INTEGER REFERENCES users(id)
            );
CREATE TABLE cukcuk_invoice_items(
              detail_id TEXT PRIMARY KEY, ref_id TEXT NOT NULL REFERENCES cukcuk_invoices(ref_id),
              item_code TEXT NOT NULL, item_name TEXT NOT NULL,
              quantity TEXT NOT NULL, amount TEXT NOT NULL, unit_name TEXT NOT NULL DEFAULT ''
            );
CREATE TABLE cukcuk_invoice_payments(
              payment_id TEXT PRIMARY KEY, ref_id TEXT NOT NULL REFERENCES cukcuk_invoices(ref_id),
              payment_type INTEGER NOT NULL, amount TEXT NOT NULL
            );
CREATE TABLE cukcuk_invoices(
              ref_id TEXT PRIMARY KEY, ref_no TEXT NOT NULL, ref_date TEXT NOT NULL,
              branch_id TEXT NOT NULL, payment_status INTEGER NOT NULL,
              table_name TEXT NOT NULL DEFAULT '',
              total_amount TEXT NOT NULL, cash_amount TEXT NOT NULL,
              card_amount TEXT NOT NULL, modified_date TEXT NOT NULL
            );
CREATE TABLE cukcuk_sync_runs(
              id INTEGER PRIMARY KEY, from_date TEXT NOT NULL, to_date TEXT NOT NULL,
              completed_at TEXT NOT NULL, invoice_count INTEGER NOT NULL
            );
CREATE TABLE daily_stock_counts(
              day TEXT NOT NULL, phase TEXT NOT NULL CHECK(phase IN ('opening','closing')),
              item_id INTEGER NOT NULL REFERENCES items(id), quantity TEXT NOT NULL,
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id), cartons TEXT, loose_units TEXT,
              PRIMARY KEY(day,phase,item_id)
            );
CREATE TABLE daily_stock_opening_overrides(
              day TEXT NOT NULL, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id),
              PRIMARY KEY(day,item_id)
            );
CREATE TABLE daily_usage(
              day TEXT NOT NULL, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
              PRIMARY KEY(day,item_id)
            );
CREATE TABLE items(
              id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
              group_name TEXT NOT NULL, unit TEXT NOT NULL,
              min_stock TEXT NOT NULL DEFAULT '0', active INTEGER NOT NULL DEFAULT 1
            , units_per_carton INTEGER);
CREATE TABLE kiosk_pins(
              user_id INTEGER PRIMARY KEY REFERENCES users(id), pin_hash TEXT NOT NULL
            );
CREATE TABLE order_incidents(
              id INTEGER PRIMARY KEY, bill_ref TEXT NOT NULL, category TEXT NOT NULL,
              description TEXT NOT NULL, amount INTEGER NOT NULL DEFAULT 0,
              user_id INTEGER REFERENCES users(id),
              status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id)
            );
CREATE TABLE recipes(
              item_code TEXT NOT NULL, ingredient_id INTEGER NOT NULL REFERENCES items(id),
              quantity_per_unit TEXT NOT NULL, PRIMARY KEY(item_code,ingredient_id)
            );
CREATE TABLE runner_events(
              id INTEGER PRIMARY KEY, detail_id TEXT NOT NULL REFERENCES runner_items(detail_id),
              kind TEXT NOT NULL, created_at TEXT NOT NULL, quantity TEXT, added_quantity TEXT,
              dish_name TEXT, table_name TEXT, order_no TEXT, remaining_text TEXT
            );
CREATE TABLE runner_items(
              detail_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES runner_orders(order_id),
              item_name TEXT NOT NULL, item_key TEXT, quantity TEXT NOT NULL,
              source_quantity TEXT NOT NULL, served_quantity TEXT NOT NULL DEFAULT '0',
              first_seen_at TEXT NOT NULL,
              served_at TEXT, canceled_at TEXT, last_alert_at TEXT,
              kds_status INTEGER
            );
CREATE TABLE runner_monitor_state(
              id INTEGER PRIMARY KEY CHECK(id=1), last_success_at TEXT,
              last_error TEXT, updated_at TEXT NOT NULL
            );
CREATE TABLE runner_orders(
              order_id TEXT PRIMARY KEY, order_no TEXT NOT NULL, table_name TEXT NOT NULL,
              order_status INTEGER NOT NULL, last_seen_at TEXT NOT NULL
            );
CREATE TABLE sales_imports(
              id INTEGER PRIMARY KEY, source_row_id TEXT NOT NULL UNIQUE,
              shift_id INTEGER NOT NULL REFERENCES cash_shifts(id),
              item_id INTEGER REFERENCES items(id),
              quantity TEXT NOT NULL, amount INTEGER NOT NULL,
              method TEXT NOT NULL CHECK(method IN ('cash','bank')),
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
            );
CREATE TABLE sessions(
              token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
              csrf TEXT NOT NULL, expires_at TEXT NOT NULL
            );
CREATE TABLE stock_counts(
              id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES items(id),
              book_qty TEXT NOT NULL, counted_qty TEXT NOT NULL,
              difference TEXT NOT NULL, note TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
              reviewed_at TEXT, reviewed_by INTEGER REFERENCES users(id)
            );
CREATE TABLE stock_moves(
              id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, kind TEXT NOT NULL, reason TEXT NOT NULL,
              reference TEXT NOT NULL DEFAULT '', shift_id INTEGER REFERENCES cash_shifts(id),
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
            );
CREATE TABLE users(
              id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
              display_name TEXT NOT NULL, role TEXT NOT NULL,
              department TEXT NOT NULL DEFAULT 'other',
              password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
            );
CREATE TABLE work_shifts(
              id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
              starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
              checked_in_at TEXT, checked_out_at TEXT,
              note TEXT NOT NULL DEFAULT ''
            );
CREATE TABLE zone_assignments(
          id INTEGER PRIMARY KEY, zone_id INTEGER NOT NULL REFERENCES zones(id),
          user_id INTEGER NOT NULL REFERENCES users(id),
          starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
        );
CREATE TABLE zone_observation_items(
          observation_id INTEGER NOT NULL REFERENCES zone_observations(id),
          group_name TEXT NOT NULL, observed_qty TEXT NOT NULL,
          ordered_qty TEXT, surplus_qty TEXT,
          PRIMARY KEY(observation_id,group_name)
        );
CREATE TABLE zone_observations(
          id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, zone_id INTEGER REFERENCES zones(id),
          observed_at TEXT NOT NULL, observed_by INTEGER NOT NULL REFERENCES users(id),
          order_as_of TEXT NOT NULL, mapping_status TEXT NOT NULL,
          assigned_staff_json TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'open', resolution_note TEXT NOT NULL DEFAULT '',
          resolved_at TEXT, resolved_by INTEGER REFERENCES users(id)
        );
CREATE TABLE zone_shift_notes(
          report_id INTEGER NOT NULL REFERENCES zone_shift_reports(id),
          invoice_id TEXT NOT NULL, note TEXT NOT NULL,
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id),
          PRIMARY KEY(report_id,invoice_id)
        );
CREATE TABLE zone_shift_reports(
          id INTEGER PRIMARY KEY, day TEXT NOT NULL, generated_at TEXT NOT NULL,
          generated_by INTEGER NOT NULL REFERENCES users(id), report_json TEXT NOT NULL
        );
CREATE TABLE zone_tables(
          table_name TEXT PRIMARY KEY, zone_id INTEGER NOT NULL REFERENCES zones(id),
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id)
        );
CREATE TABLE zone_tobacco_allocations(
          day TEXT NOT NULL, zone_id INTEGER NOT NULL REFERENCES zones(id),
          item_code TEXT NOT NULL CHECK(item_code IN ('TNN','TM')),
          issued TEXT, returned TEXT, ending TEXT,
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id),
          PRIMARY KEY(day,zone_id,item_code)
        );
CREATE TABLE zones(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
        );
CREATE INDEX idx_cukcuk_items_code ON cukcuk_invoice_items(item_code);
CREATE INDEX idx_zone_assignment_window
          ON zone_assignments(zone_id,starts_at,ends_at);
CREATE INDEX idx_zone_shift_day ON zone_shift_reports(day,id);
COMMIT;
