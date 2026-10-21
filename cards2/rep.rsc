{
:local t "";
:foreach u in=[/ip hotspot user find where comment~"^Kanary_C"] do={ :do { :local c [/ip hotspot user get $u comment]; :local n [/ip hotspot user get $u name]; :local bi [/ip hotspot user get $u bytes-in]; :local bo [/ip hotspot user get $u bytes-out]; :local ut [/ip hotspot user get $u uptime]; :local ds [/ip hotspot user get $u disabled]; :set t ($t . "v" . $n . "|" . ($bi + $bo) . "|" . [:tostr $ut] . "|" . [:tostr $ds] . "|" . $c . "\n") } on-error={} };
:set t ($t . "c" . [/system clock get date] . "|" . [/system clock get time] . "|" . [:tostr [/system clock get gmt-offset]] . "\n");
/tool fetch url="https://10.0.2.2:8443/agent/cards?job=lab&s=e" http-method=post http-header-field="X-Kanaria-Token: eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee,Content-Type: text/plain" http-data=$t check-certificate=yes output=none;
}
