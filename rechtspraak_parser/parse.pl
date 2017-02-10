:- use_module(library(sgml)).
:- use_module(library(lists)).
:- use_module(library(dcg/basics)).

example(File, DOM) :-
	load_xml(File, DOM, []).

meta(DOM,Meta) :-
	xpath(DOM, //('rdf:RDF')/('rdf:Description'), Meta).

meta_property(Meta, Property, Value) :-
	xpath(Meta, //(Property), element(_,_,Values)),
	atomic_list_concat(Values, Value).

inhoudsindicatie(DOM, ID, Props, Inhoud) :-
	xpath(DOM, //('inhoudsindicatie'), element(_,Attrs,Inhoud)),
	select('id'=ID, Attrs, Attrs2),
	bagof(A-V, member(A=V, Attrs2), Props).

uitspraak(DOM, ID, Props, Inhoud) :-
	xpath(DOM, //('uitspraak'), element(_,Attrs,Inhoud)),
	select('id'=ID, Attrs, Attrs2),
	bagof(A-V, member(A=V, Attrs2), Props).

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

case(DOM, ID, Props, Inhoud, Uitspraak) :-
	meta(DOM, M),
	findall(Attribute-Value,
		(
			prop(Attribute),
			meta_property(M, Attribute, Value)
		),
		AllProps),
	select('dcterms:identifier'-ID, AllProps, Props),
	inhoudsindicatie(DOM, _IHID, _IHProps, Inhoud),
	uitspraak(DOM, _UitID, _UitProps, Uitspraak).

% example:
% ?- example('OpenDataUitspraken/2016/ECLI_NL_RBLIM_2016_1790.xml',D), case(D,ID,P).

