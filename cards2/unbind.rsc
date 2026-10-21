{
:foreach u in=[/ip hotspot user find where (comment~"^Kanary_C b2222222;" or (name="b2222222" and comment="Kanary_C"))] do={ :local n [/ip hotspot user get $u name]; :if ($n != "b2222222") do={ /ip hotspot user set $u name="b2222222" password="b2222222"; :do { /ip hotspot active remove [find where user=$n] } on-error={} } };
}
