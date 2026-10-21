{
:foreach u in=[/ip hotspot user find where (comment~"^Kanary_C a1111111;" or (name="a1111111" and comment="Kanary_C"))] do={ :local n [/ip hotspot user get $u name]; :do { /ip hotspot active remove [find where user=$n] } on-error={}; /ip hotspot user remove $u };
:foreach u in=[/ip hotspot user find where (comment~"^Kanary_C b2222222;" or (name="b2222222" and comment="Kanary_C"))] do={ :local n [/ip hotspot user get $u name]; :do { /ip hotspot active remove [find where user=$n] } on-error={}; /ip hotspot user remove $u };
:foreach u in=[/ip hotspot user find where (comment~"^Kanary_C c3333333;" or (name="c3333333" and comment="Kanary_C"))] do={ :local n [/ip hotspot user get $u name]; :do { /ip hotspot active remove [find where user=$n] } on-error={}; /ip hotspot user remove $u };
:foreach u in=[/ip hotspot user find where (comment~"^Kanary_C d4444444;" or (name="d4444444" and comment="Kanary_C"))] do={ :local n [/ip hotspot user get $u name]; :do { /ip hotspot active remove [find where user=$n] } on-error={}; /ip hotspot user remove $u };
:do { :if ([:len [/ip hotspot user find where profile="Lab Monthly - 2026-10-21 - MAC"]] = 0) do={ /ip hotspot user profile remove [find where name="Lab Monthly - 2026-10-21 - MAC"] } } on-error={};
:do { :if ([:len [/ip hotspot user find where profile="Lab Daily - 2026-10-21"]] = 0) do={ /ip hotspot user profile remove [find where name="Lab Daily - 2026-10-21"] } } on-error={};
:do { :if ([:len [/ip hotspot user find where profile="Lab Created - 2026-10-21"]] = 0) do={ /ip hotspot user profile remove [find where name="Lab Created - 2026-10-21"] } } on-error={};
:do { /system scheduler remove [find where name="Kanaria-expire"] } on-error={};
}
