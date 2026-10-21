{
:local src [/ip hotspot user profile get [find where name="Lab Daily - 2026-10-21"] on-login];
:local f [:parse (":local user \"c3333333\"; :local \"mac-address\" \"02:00:00:00:00:02\"; " . $src)];
$f;
}
