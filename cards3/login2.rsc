{
:local src [/ip hotspot user profile get [find where name="Lab MAC - 2026-10-21 - MAC"] on-login];
:local f [:parse (":local user \"43448412\"; :local \"mac-address\" \"02:00:00:00:00:01\"; " . $src)];
$f;
}
