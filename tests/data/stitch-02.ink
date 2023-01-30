-> travel

=== travel ===
= question
Where do you want to go?
* Paris
  -> paris
* [London] -> london
* Madrid
  Noone wants to go there!
  -> end

= london
We arrived into London.
-> end

= paris
We arrived into Paris.
-> end.loop

=== end ===
The end. -> END
= loop
-> travel.question
