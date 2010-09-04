fun(Keys, Values, ReReduce) ->
	Debet = lists:sum([D || {[{<<"debet">>, D}, {<<"kredit">>, K}]} <- Values ]),
	Kredit = lists:sum([K || {[{<<"debet">>, D}, {<<"kredit">>, K}]} <- Values ]),
	{[{debet, erlang:round(Debet*100.0)/100.0}, {kredit, erlang:round(Kredit*100.0)/100.0}]}
end.
