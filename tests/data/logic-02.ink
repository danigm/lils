-> travel

=== travel ===

At the Airport
* paris -> paris
* {paris} london -> london
* {paris && not travel.london} madrid -> spain.madrid
* {paris > 1 && travel.london && spain.madrid} home -> END

= london
You are in London
-> travel

=== paris ===
You are in Paris
-> travel

=== spain ===
= madrid
You are in Madrid
-> travel
