{
:local src [/ip hotspot user profile get [find where name="Lab Created - 2026-10-21"] on-login];
:local f [:parse (":local user \"d4444444\"; :local \"mac-address\" \"02:00:00:00:00:03\"; " . $src)];
$f;
}
