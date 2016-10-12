:- use_module(library(sgml)).
:- use_module(library(lists)).
:- use_module(library(dcg/basics)).

example(File,DOM) :-
	load_xml(File,DOM,[]).

meta(DOM,Meta) :-
	xpath(DOM,//('rdf:RDF')/('rdf:Description'),Meta).

meta_property(Meta,Property,Value) :-
	xpath(Meta,//(Property),element(_,_,Values)),
	member(Value,Values).

prop('dcterms:identifier').
prop('dcterms:format').
prop('dcterms:accessRights').
prop('dcterms:modified').
prop('dcterms:issued').
prop('dcterms:publisher').
prop('dcterms:language').
prop('dcterms:creator').
prop('dcterms:date').
prop('dcterms:type').
prop('dcterms:coverage').
prop('dcterms:subject').
prop('psi:zaaknummer').

case(DOM,ID,Props) :-
	meta(DOM,M),
	findall(Attribute-Value,
		(
			prop(Attribute),
			meta_property(M,Attribute,Value)
		),
		AllProps),
	select('dcterms:identifier'-ID,AllProps,Props).

% example:
% ?- example('OpenDataUitspraken/2016/ECLI_NL_RBLIM_2016_1790.xml',D), case(D,ID,P).

