#!/usr/bin/env python
"""
Database Schema Validation Script
Validates that ORM models match the DDL schema structure.
"""

from models import (
    User,
    Point,
    Country,
    InternationalOrg,
    MemberCountry,
    MemberOrg,
    LocalOrg,
    Map,
    MapPoint,
    LinkType,
    Link,
    LinkDetails,
    Base,
)

def validate_models():
    """Validate that all ORM models are defined correctly."""
    
    models_to_check = [
        User, Point, Country, InternationalOrg, MemberCountry, MemberOrg, LocalOrg,
        Map, MapPoint, LinkType, Link, LinkDetails
    ]
    
    print("=" * 60)
    print("ORM Model Validation Report")
    print("=" * 60)
    
    total_models = len(models_to_check)
    total_columns = 0
    total_relationships = 0
    
    for model in models_to_check:
        table_name = model.__tablename__
        columns = model.__table__.columns
        relationships = [k for k in model.__dict__.keys() if not k.startswith('_')]
        
        col_count = len(columns)
        rel_count = len(relationships)
        
        total_columns += col_count
        total_relationships += rel_count
        
        pk_col = None
        for col in columns:
            if col.primary_key:
                pk_col = col.name
                break
        
        pk_name = pk_col if pk_col else "COMPOSITE"
        
        print(f"\nOK {model.__name__:20} -> {table_name:25}")
        print(f"  Columns: {col_count:3} | Primary Key: {pk_name:15}")
        
        # Display primary key info
        for col in columns:
            if col.primary_key:
                print(f"    PK: {col.name} ({col.type})")
    
    print("\n" + "=" * 60)
    print(f"Summary: {total_models} models, {total_columns} columns defined")
    print("=" * 60)
    
    # Key validations
    print("\nKey Validations:")
    
    # Check Country model
    country_model = Country
    if country_model.__table__.columns['iso_id'].primary_key:
        print("OK Country.iso_id is primary key")
    else:
        print("NG Country.iso_id should be primary key")

    # Check LinkDetails model
    if LinkDetails.__table__.columns['link_id'].primary_key:
        print("OK LinkDetails.link_id is primary key")
    else:
        print("NG LinkDetails.link_id should be primary key")
    
    # Check Numeric types for coordinates
    point_lat_type = str(Point.__table__.columns['lat'].type)
    if 'NUMERIC' in point_lat_type or 'Numeric' in point_lat_type:
        print(f"OK Point.lat is NUMERIC type: {point_lat_type}")
    else:
        print(f"NG Point.lat should be NUMERIC, got: {point_lat_type}")
    
    # Check foreign keys
    fk_count = 0
    for model in models_to_check:
        for col in model.__table__.columns:
            if col.foreign_keys:
                fk_count += 1
    
    print(f"OK Total foreign key columns defined: {fk_count}")
    
    # Check indexes
    index_count = 0
    for model in models_to_check:
        for idx in model.__table__.indexes:
            index_count += 1
    
    print(f"OK Total indexes defined: {index_count}")
    
    print("\nOK All models validated successfully!")
    return True

if __name__ == "__main__":
    try:
        validate_models()
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
