#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_markup
----------------------------------

Tests for `markup` module.
"""
from __future__ import unicode_literals

import pytest

from mmworkbench import markup

from mmworkbench.core import Entity, EntityGroup, NestedEntity, ProcessedQuery, QueryEntity, Span

MARKED_UP_STRS = [
    'show me houses under {[600,000|sys:number] dollars|price}',
    'show me houses under {[$600,000|sys:number]|price}',
    'show me houses under {[1.5|sys:number] million dollars|price}',
    'play {s.o.b.|track}',
    "what's on at {[8 p.m.|sys:time]|range}?",
    'is {s.o.b.|show} gonna be on at {[8 p.m.|sys:time]|range}?',
    'this is a {role model|type|role}',
    'this query has no entities'
]

MARKED_DOWN_STRS = [
    'show me houses under 600,000 dollars',
    'show me houses under $600,000',
    'show me houses under 1.5 million dollars',
    'play s.o.b.',
    "what's on at 8 p.m.?",
    'is s.o.b. gonna be on at 8 p.m.?',
    'this is a role model',
    'this query has no entities'
]


@pytest.mark.mark_down
def test_mark_down():
    """Tests the mark down function"""
    text = 'is {s.o.b.|show} gonna be {{on at 8 p.m.|sys:time}|range}?'
    marked_down = markup.mark_down(text)
    assert marked_down == 'is s.o.b. gonna be on at 8 p.m.?'


@pytest.mark.load
def test_load_basic_query(query_factory):
    """Tests loading a basic query with no entities"""
    markup_text = 'This is a test query string'

    processed_query = markup.load_query(markup_text, query_factory)
    assert processed_query
    assert processed_query.query


@pytest.mark.load
def test_load_entity(query_factory):
    """Tests loading a basic query with an entity"""
    markup_text = 'When does the {Elm Street|store_name} store close?'

    processed_query = markup.load_query(markup_text, query_factory)

    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]
    assert entity.span.start == 14
    assert entity.span.end == 23
    assert entity.normalized_text == 'elm street'
    assert entity.entity.type == 'store_name'
    assert entity.entity.text == 'Elm Street'


@pytest.mark.load
@pytest.mark.system
def test_load_system(query_factory):
    """Tests loading a query with a system entity"""
    text = 'show me houses under {600,000 dollars|sys:currency}'
    processed_query = markup.load_query(text, query_factory)

    assert processed_query
    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]
    assert entity.text == '600,000 dollars'
    assert entity.entity.type == 'sys:currency'
    assert entity.span.start == 21
    assert not isinstance(entity.entity.value, str)

    assert entity.entity.value == {'unit': '$', 'value': 600000}


@pytest.mark.load
@pytest.mark.system
@pytest.mark.nested
def test_load_nested(query_factory):
    """Tests loading a query with a nested system entity"""
    text = 'show me houses under {{600,000|sys:number} dollars|price}'

    processed_query = markup.load_query(text, query_factory)

    assert processed_query
    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]
    assert entity.text == '600,000 dollars'
    assert entity.entity.type == 'price'

    assert entity.span == Span(21, 35)

    assert not isinstance(entity.entity.value, str)
    assert 'children' in entity.entity.value
    assert len(entity.entity.value['children']) == 1
    nested = entity.entity.value['children'][0]
    assert nested.text == '600,000'
    assert nested.span == Span(0, 6)
    assert nested.entity.type == 'sys:number'
    assert nested.entity.value == {'value': 600000}


@pytest.mark.load
@pytest.mark.system
@pytest.mark.nested
def test_load_nested_2(query_factory):
    """Tests loading a query with a nested system entity"""
    text = 'show me houses under {${600,000|sys:number}|price}'
    processed_query = markup.load_query(text, query_factory)
    assert processed_query
    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]
    assert entity.text == '$600,000'
    assert entity.entity.type == 'price'
    assert entity.span == Span(21, 28)

    assert not isinstance(entity.entity.value, str)
    assert 'children' in entity.entity.value
    assert len(entity.entity.value['children']) == 1
    nested = entity.entity.value['children'][0]
    assert nested.text == '600,000'
    assert nested.entity.value == {'value': 600000}
    assert nested.span == Span(1, 7)


@pytest.mark.load
@pytest.mark.system
@pytest.mark.nested
def test_load_nested_3(query_factory):
    """Tests loading a query with a nested system entity"""
    text = 'show me houses under {{1.5 million|sys:number} dollars|price}'
    processed_query = markup.load_query(text, query_factory)

    assert processed_query


@pytest.mark.load
@pytest.mark.system
@pytest.mark.nested
def test_load_nested_4(query_factory):
    """Tests dumping a query with multiple nested system entities"""
    text = 'show me houses {between {600,000|sys:number} and {1,000,000|sys:number} dollars|price}'
    processed_query = markup.load_query(text, query_factory)

    assert processed_query
    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]
    assert entity.text == 'between 600,000 and 1,000,000 dollars'
    assert entity.entity.type == 'price'
    assert entity.span == Span(15, 51)

    assert not isinstance(entity.entity.value, str)
    assert 'children' in entity.entity.value
    assert len(entity.entity.value['children']) == 2
    lower, upper = entity.entity.value['children']

    assert lower.text == '600,000'
    assert lower.entity.value == {'value': 600000}
    assert lower.span == Span(8, 14)

    assert upper.text == '1,000,000'
    assert upper.entity.value == {'value': 1000000}
    assert upper.span == Span(20, 28)


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars(query_factory):
    """Tests loading a query with special characters"""
    text = 'play {s.o.b.|track}'
    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities)
    entity = entities[0]
    assert entity.text == 's.o.b.'
    assert entity.normalized_text == 's o b'
    assert entity.span.start == 5
    assert entity.span.end == 10


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars_2(query_factory):
    """Tests loading a query with special characters"""
    text = "what's on at {{8 p.m.|sys:time}|range}?"
    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities) == 1

    entity = entities[0]
    assert entity.text == '8 p.m.'
    assert entity.normalized_text == '8 p m'
    assert entity.span == Span(13, 18)
    assert entity.entity.type == 'range'

    nested = entity.entity.value['children'][0]
    assert nested.text == '8 p.m.'
    assert nested.span == Span(0, 5)
    assert nested.entity.type == 'sys:time'
    assert nested.entity.value['value']


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars_3(query_factory):
    """Tests loading a query with special characters"""
    text = 'is {s.o.b.|show} gonna be {{on at 8 p.m.|sys:time}|range}?'
    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    expected_entity = QueryEntity.from_query(processed_query.query, Span(3, 8), entity_type='show')
    assert entities[0] == expected_entity

    assert entities[1].entity.type == 'range'
    assert entities[1].span == Span(19, 30)
    assert 'children' in entities[1].entity.value
    assert entities[1].entity.value['children'][0].entity.type == 'sys:time'


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars_4(query_factory):
    """Tests loading a query with special characters"""
    text = 'is {s.o.b.|show} ,, gonna be on at {{8 p.m.|sys:time}|range}?'

    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    expected_entity = QueryEntity.from_query(processed_query.query, Span(3, 8), entity_type='show')
    assert entities[0] == expected_entity

    assert entities[1].entity.type == 'range'
    assert entities[1].span == Span(28, 33)
    assert 'children' in entities[1].entity.value
    assert entities[1].entity.value['children'][0].entity.type == 'sys:time'


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars_5(query_factory):
    """Tests loading a query with special characters"""
    text = 'what christmas movies   are  , showing at {{8pm|sys:time}|range}'

    processed_query = markup.load_query(text, query_factory)

    assert len(processed_query.entities) == 1

    entity = processed_query.entities[0]

    assert entity.span == Span(42, 44)
    assert entity.normalized_text == '8pm'


@pytest.mark.load
@pytest.mark.special
def test_load_special_chars_6(query_factory):
    """Tests loading a query with special characters"""
    text = "what's on {after {8 p.m.|sys:time}|range}?"
    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities) == 1

    assert entities[0].text == 'after 8 p.m.'
    assert entities[0].normalized_text == 'after 8 p m'
    assert entities[0].span == Span(10, 21)


@pytest.mark.load
@pytest.mark.group
def test_load_group(query_factory):
    """Tests loading a query with an entity group"""
    text = "a [{large|size} {latte|product} with {nonfat milk|option}|product] please"

    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities) == 3

    assert entities[0].text == 'large'
    assert entities[0].entity.type == 'size'
    assert entities[0].span == Span(2, 6)

    assert entities[1].text == 'latte'
    assert entities[1].entity.type == 'product'
    assert entities[1].span == Span(8, 12)

    assert entities[2].text == 'nonfat milk'
    assert entities[2].entity.type == 'option'
    assert entities[2].span == Span(19, 29)

    assert len(processed_query.entity_groups) == 1

    assert processed_query.entity_groups[0].head == entities[1]
    assert len(processed_query.entity_groups[0].dependents) == 2


@pytest.mark.load
@pytest.mark.group
def test_load_group_nested(query_factory):
    """Tests loading a query with a nested entity group"""
    text = ('Order [{one|quantity} {large|size} {Tesora|product} with [{medium|size} '
            '{cream|option}|option] and [{medium|size} {sugar|option}|option]|product]')

    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities) == 7

    assert entities[0].text == 'one'
    assert entities[0].entity.type == 'quantity'
    assert entities[0].span == Span(6, 8)

    assert entities[1].text == 'large'
    assert entities[1].entity.type == 'size'
    assert entities[1].span == Span(10, 14)

    assert entities[2].text == 'Tesora'
    assert entities[2].entity.type == 'product'
    assert entities[2].span == Span(16, 21)

    assert entities[3].text == 'medium'
    assert entities[3].entity.type == 'size'
    assert entities[3].span == Span(28, 33)

    assert entities[4].text == 'cream'
    assert entities[4].entity.type == 'option'
    assert entities[4].span == Span(35, 39)

    assert entities[5].text == 'medium'
    assert entities[5].entity.type == 'size'
    assert entities[5].span == Span(45, 50)

    assert entities[6].text == 'sugar'
    assert entities[6].entity.type == 'option'
    assert entities[6].span == Span(52, 56)

    assert len(processed_query.entity_groups) == 1

    product_group = processed_query.entity_groups[0]

    assert product_group.head == entities[2]

    assert product_group.dependents[0] == entities[0]
    assert product_group.dependents[1] == entities[1]

    assert len(product_group.dependents) == 4

    assert product_group.dependents[2].head == entities[4]
    assert product_group.dependents[2].dependents == [entities[3]]

    assert product_group.dependents[3].head == entities[6]
    assert product_group.dependents[3].dependents == [entities[5]]


@pytest.mark.load
@pytest.mark.group
def test_load_groups(query_factory):
    """Tests loading a query with multiple top level entity groups"""
    text = ('Order [{one|quantity} {large|size} {Tesora|product} with '
            '[{medium|size} {cream|option}|option]|product] from '
            '[{Philz|store} in {Downtown Sunnyvale|location}|store]')

    processed_query = markup.load_query(text, query_factory)
    entities = processed_query.entities

    assert len(entities) == 7

    assert entities[0].text == 'one'
    assert entities[0].entity.type == 'quantity'
    assert entities[0].span == Span(6, 8)

    assert entities[1].text == 'large'
    assert entities[1].entity.type == 'size'
    assert entities[1].span == Span(10, 14)

    assert entities[2].text == 'Tesora'
    assert entities[2].entity.type == 'product'
    assert entities[2].span == Span(16, 21)

    assert entities[3].text == 'medium'
    assert entities[3].entity.type == 'size'
    assert entities[3].span == Span(28, 33)

    assert entities[4].text == 'cream'
    assert entities[4].entity.type == 'option'
    assert entities[4].span == Span(35, 39)

    assert entities[5].text == 'Philz'
    assert entities[5].entity.type == 'store'
    assert entities[5].span == Span(46, 50)

    assert entities[6].text == 'Downtown Sunnyvale'
    assert entities[6].entity.type == 'location'
    assert entities[6].span == Span(55, 72)

    assert len(processed_query.entity_groups) == 2

    product_group = processed_query.entity_groups[0]

    assert product_group.head == entities[2]

    assert product_group.dependents[0] == entities[0]
    assert product_group.dependents[1] == entities[1]

    assert len(product_group.dependents) == 3

    assert product_group.dependents[2].head == entities[4]
    assert product_group.dependents[2].dependents == [entities[3]]

    store_group = processed_query.entity_groups[1]

    assert store_group.head == entities[5]
    assert store_group.dependents == [entities[6]]


@pytest.mark.dump
def test_dump_basic(query_factory):
    """Tests dumping a basic query"""
    query_text = 'A basic query'
    query = query_factory.create_query(query_text)
    processed_query = ProcessedQuery(query)

    assert markup.dump_query(processed_query) == query_text


@pytest.mark.dump
def test_dump_entity(query_factory):
    """Tests dumping a basic query with an entity"""
    query_text = 'When does the Elm Street store close?'
    query = query_factory.create_query(query_text)
    entities = [QueryEntity.from_query(query, Span(14, 23), entity_type='store_name')]
    processed_query = ProcessedQuery(query, entities=entities)

    markup_text = 'When does the {Elm Street|store_name} store close?'
    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
def test_dump_entities(query_factory):
    """Tests dumping a basic query with two entities"""
    query_text = 'When does the Elm Street store close on Monday?'
    query = query_factory.create_query(query_text)
    entities = [QueryEntity.from_query(query, Span(14, 23), entity_type='store_name'),
                QueryEntity.from_query(query, Span(40, 45), entity_type='sys:time')]
    processed_query = ProcessedQuery(query, entities=entities)

    markup_text = 'When does the {Elm Street|store_name} store close on {Monday|sys:time}?'
    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
@pytest.mark.nested
def test_dump_nested(query_factory):
    """Tests dumping a query with a nested system entity"""
    query_text = 'show me houses under 600,000 dollars'
    query = query_factory.create_query(query_text)

    nested = NestedEntity.from_query(query, Span(0, 6), parent_offset=21, entity_type='sys:number')
    raw_entity = Entity('600,000 dollars', 'price', value={'children': [nested]})
    entities = [QueryEntity.from_query(query, Span(21, 35), entity=raw_entity)]
    processed_query = ProcessedQuery(query, entities=entities)

    markup_text = 'show me houses under {{600,000|sys:number} dollars|price}'
    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
@pytest.mark.nested
def test_dump_multi_nested(query_factory):
    """Tests dumping a query with multiple nested system entities"""
    query_text = 'show me houses between 600,000 and 1,000,000 dollars'
    query = query_factory.create_query(query_text)

    lower = NestedEntity.from_query(query, Span(8, 14), parent_offset=15, entity_type='sys:number')
    upper = NestedEntity.from_query(query, Span(20, 28), parent_offset=15, entity_type='sys:number')
    raw_entity = Entity('between 600,000 dollars and 1,000,000', 'price',
                        value={'children': [lower, upper]})
    entities = [QueryEntity.from_query(query, Span(15, 51), entity=raw_entity)]
    processed_query = ProcessedQuery(query, entities=entities)

    markup_text = ('show me houses {between {600,000|sys:number} and '
                   '{1,000,000|sys:number} dollars|price}')

    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
@pytest.mark.group
def test_dump_group(query_factory):
    """Tests dumping a query with an entity group"""
    query_text = 'a large latte with nonfat milk please'
    query = query_factory.create_query(query_text)

    size = QueryEntity.from_query(query, Span(2, 6), entity_type='size')
    product = QueryEntity.from_query(query, Span(8, 12), entity_type='product')
    option = QueryEntity.from_query(query, Span(19, 29), entity_type='option')

    group = EntityGroup(product, [size, option])

    processed_query = ProcessedQuery(query, entities=[size, product, option],
                                     entity_groups=[group])
    markup_text = "a [{large|size} {latte|product} with {nonfat milk|option}|product] please"

    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
@pytest.mark.group
def test_dump_group_nested(query_factory):
    """Tests dumping a query with nested entity groups"""
    query_text = 'Order one large Tesora with medium cream and medium sugar'

    query = query_factory.create_query(query_text)
    entities = [
        QueryEntity.from_query(query, Span(6, 8), entity_type='quantity'),
        QueryEntity.from_query(query, Span(10, 14), entity_type='size'),
        QueryEntity.from_query(query, Span(16, 21), entity_type='product'),
        QueryEntity.from_query(query, Span(28, 33), entity_type='size'),
        QueryEntity.from_query(query, Span(35, 39), entity_type='option'),
        QueryEntity.from_query(query, Span(45, 50), entity_type='size'),
        QueryEntity.from_query(query, Span(52, 56), entity_type='option')
    ]
    groups = [
        EntityGroup(entities[2], [
            entities[0],
            entities[1],
            EntityGroup(entities[4], [entities[3]]),
            EntityGroup(entities[6], [entities[5]])
        ])
    ]

    processed_query = ProcessedQuery(query, entities=entities, entity_groups=groups)

    markup_text = ('Order [{one|quantity} {large|size} {Tesora|product} with [{medium|size} '
                   '{cream|option}|option] and [{medium|size} {sugar|option}|option]|product]')

    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.dump
@pytest.mark.group
def test_dump_groups(query_factory):
    """Tests dumping a query with multiple top level entity groups"""
    query_text = 'Order one large Tesora with medium cream from Philz in Downtown Sunnyvale'

    query = query_factory.create_query(query_text)
    entities = [
        QueryEntity.from_query(query, Span(6, 8), entity_type='quantity'),
        QueryEntity.from_query(query, Span(10, 14), entity_type='size'),
        QueryEntity.from_query(query, Span(16, 21), entity_type='product'),
        QueryEntity.from_query(query, Span(28, 33), entity_type='size'),
        QueryEntity.from_query(query, Span(35, 39), entity_type='option'),
        QueryEntity.from_query(query, Span(46, 50), entity_type='store'),
        QueryEntity.from_query(query, Span(55, 72), entity_type='location')
    ]
    groups = [
        EntityGroup(entities[2], [
            entities[0],
            entities[1],
            EntityGroup(entities[4], [entities[3]]),
        ]),
        EntityGroup(entities[5], [entities[6]])
    ]

    processed_query = ProcessedQuery(query, entities=entities, entity_groups=groups)

    markup_text = ('Order [{one|quantity} {large|size} {Tesora|product} with '
                   '[{medium|size} {cream|option}|option]|product] from '
                   '[{Philz|store} in {Downtown Sunnyvale|location}|store]')

    assert markup.dump_query(processed_query) == markup_text


@pytest.mark.load
@pytest.mark.dump
@pytest.mark.group
def test_load_dump_groups(query_factory):
    """Tests that load_query and dump_query are reversible"""
    text = ('Order [{one|quantity} {large|size} {Tesora|product} with '
            '[{medium|size} {cream|option}|option]|product] from '
            '[{Philz|store} in {Downtown Sunnyvale|location}|store]')

    processed_query = markup.load_query(text, query_factory)

    markup_text = markup.dump_query(processed_query)

    assert text == markup_text


@pytest.mark.load
@pytest.mark.dump
def test_load_dump_2(query_factory):
    """Tests that load_query and dump_query are reversible"""
    text = ("i'm extra hungry get me a {chicken leg|dish}, [{1|quantity} "
            "{kheema nan|dish}|dish] [{2|quantity} regular {nans|dish}|dish] "
            "[{one|quantity} {chicken karahi|dish}|dish], [{1|quantity} "
            "{saag paneer|dish}|dish] and [{1|quantity} {chicken biryani|dish}|dish]")

    processed_query = markup.load_query(text, query_factory)

    markup_text = markup.dump_query(processed_query)

    assert text == markup_text
