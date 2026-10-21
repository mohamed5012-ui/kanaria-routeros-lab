{
:local src [/ip hotspot user profile get [find where name="Lab Monthly - 2026-10-21 - MAC"] on-login];
:local f [:parse (":local user \"02:00:00:00:00:01\"; :local \"mac-address\" \"02:00:00:00:00:01\"; " . $src)];
$f;
}
