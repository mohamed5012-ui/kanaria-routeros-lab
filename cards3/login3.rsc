{
:local src [/ip hotspot user profile get [find where name="Lab Created - 2026-10-21"] on-login];
:local f [:parse (":local user \"t5aq39f6\"; :local \"mac-address\" \"02:00:00:00:00:02\"; " . $src)];
$f;
}
