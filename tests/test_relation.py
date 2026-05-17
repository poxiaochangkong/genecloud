# tests/test_relation.py
"""
Relation module tests - comprehensive boundary condition tests
"""
import pytest
import uuid


def create_test_genealogy_and_members(client):
    """Helper to create a test genealogy with two members."""
    gid_resp = client.post('/api/genealogies', json={
        'name': f'Relation Test {uuid.uuid4().hex[:6]}',
        'surname': 'RelSurname'
    })
    if gid_resp.status_code != 201:
        return None, None, None
    gid = gid_resp.get_json()['genealogy_id']
    
    # Create parent (male for father relation)
    p_resp = client.post(f'/api/genealogies/{gid}/members', json={
        'name': 'Parent1', 'gender': 'M', 'birth_year': 1960,
        'death_year': None, 'bio': ''
    })
    if p_resp.status_code != 201:
        return gid, None, None
    pid = p_resp.get_json()['member_id']
    
    # Create child
    c_resp = client.post(f'/api/genealogies/{gid}/members', json={
        'name': 'Child1', 'gender': 'F', 'birth_year': 1990,
        'death_year': None, 'bio': ''
    })
    if c_resp.status_code != 201:
        return gid, pid, None
    cid = c_resp.get_json()['member_id']
    
    return gid, pid, cid


class TestGetParents:
    """Test get parents."""
    
    def test_get_parents_success(self, logged_in_client):
        """Test getting parents of a child."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship with 'father' type
            link_resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            assert link_resp.status_code in [200, 201]
            # Get parents
            resp = logged_in_client.get(f'/api/members/{cid}/parents')
            assert resp.status_code == 200
    
    def test_get_parents_no_parents(self, logged_in_client):
        """Test getting parents when none exist."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if cid:
            resp = logged_in_client.get(f'/api/members/{cid}/parents')
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
    
    def test_get_parents_requires_login(self, client):
        """Test getting parents without login."""
        resp = client.get('/api/members/1/parents')
        assert resp.status_code == 401


class TestGetChildren:
    """Test get children."""
    
    def test_get_children_success(self, logged_in_client):
        """Test getting children of a parent."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            link_resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            assert link_resp.status_code in [200, 201]
            # Get children
            resp = logged_in_client.get(f'/api/members/{pid}/children')
            assert resp.status_code == 200
    
    def test_get_children_requires_login(self, client):
        """Test getting children without login."""
        resp = client.get('/api/members/1/children')
        assert resp.status_code == 401


class TestAddLink:
    """Test add parent link."""
    
    def test_add_link_success(self, logged_in_client):
        """Test establishing a parent-child relationship."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid,
                'parent_id': pid,
                'relation_type': 'father'
            })
            assert resp.status_code in [200, 201]
    
    def test_add_link_self_parent(self, logged_in_client):
        """Test adding yourself as your own parent (should fail)."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': pid,
                'parent_id': pid,
                'relation_type': 'father'
            })
            # Should fail - self-reference
            assert resp.status_code in [400, 409]
    
    def test_add_link_requires_login(self, client):
        """Test adding link without login."""
        resp = client.post('/api/relations/link', json={
            'child_id': 1, 'parent_id': 2, 'relation_type': 'father'
        })
        assert resp.status_code == 401
    
    def test_add_link_invalid_relation_type(self, logged_in_client):
        """Test adding link with invalid relation_type."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid,
                'parent_id': pid,
                'relation_type': 'biological'  # Invalid - should be 'father' or 'mother'
            })
            assert resp.status_code == 400


class TestQueryAncestors:
    """Test query ancestors."""
    
    def test_query_ancestors_success(self, logged_in_client):
        """Test querying ancestors."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            resp = logged_in_client.get(f'/api/members/{cid}/ancestors')
            assert resp.status_code == 200
    
    def test_query_ancestors_requires_login(self, client):
        """Test querying ancestors without login."""
        resp = client.get('/api/members/1/ancestors')
        assert resp.status_code == 401


class TestQueryDescendants:
    """Test query descendants."""
    
    def test_query_descendants_success(self, logged_in_client):
        """Test querying descendants."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship
            logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            resp = logged_in_client.get(f'/api/members/{pid}/descendants')
            assert resp.status_code == 200
    
    def test_query_descendants_requires_login(self, client):
        """Test querying descendants without login."""
        resp = client.get('/api/members/1/descendants')
        assert resp.status_code == 401


class TestMarriageAwareness:
    """Test marriage-aware parent/child/kinship queries."""
    
    def _create_family(self, client):
        """Helper: create genealogy, father(M), mother(F), child, marriage + father link."""
        gid_resp = client.post('/api/genealogies', json={
            'name': f'Marriage Test {uuid.uuid4().hex[:6]}',
            'surname': 'TestSurname'
        })
        if gid_resp.status_code != 201:
            return None, None, None, None
        
        gid = gid_resp.get_json()['genealogy_id']
        
        # Father (male)
        f_resp = client.post(f'/api/genealogies/{gid}/members', json={
            'name': 'Father', 'gender': 'M', 'birth_year': 1960
        })
        if f_resp.status_code != 201:
            return gid, None, None, None
        fid = f_resp.get_json()['member_id']
        
        # Mother (female)
        m_resp = client.post(f'/api/genealogies/{gid}/members', json={
            'name': 'Mother', 'gender': 'F', 'birth_year': 1962
        })
        if m_resp.status_code != 201:
            return gid, fid, None, None
        mid = m_resp.get_json()['member_id']
        
        # Child
        c_resp = client.post(f'/api/genealogies/{gid}/members', json={
            'name': 'Son', 'gender': 'M', 'birth_year': 1990
        })
        if c_resp.status_code != 201:
            return gid, fid, mid, None
        cid = c_resp.get_json()['member_id']
        
        # Marriage: Father ↔ Mother
        mar_resp = client.post('/api/relations/marriage', json={
            'member_id1': fid, 'member_id2': mid, 'marriage_year': 1985
        })
        assert mar_resp.status_code in [200, 201]
        
        # Father → Son link only (not mother)
        link_resp = client.post('/api/relations/link', json={
            'child_id': cid, 'parent_id': fid, 'relation_type': 'father'
        })
        assert link_resp.status_code in [200, 201]
        
        return gid, fid, mid, cid
    
    def test_mother_gets_child_via_spouse(self, logged_in_client):
        """Mother queries children → should get son via marriage to father."""
        gid, fid, mid, cid = self._create_family(logged_in_client)
        if not cid:
            pytest.skip("Setup failed")
        
        resp = logged_in_client.get(f'/api/members/{mid}/children')
        assert resp.status_code == 200
        data = resp.get_json()
        # Mother should see the son (via_spouse)
        assert len(data) >= 1, f"Mother(children) should include son via spouse, got {data}"
        son_data = [d for d in data if d['member_id'] == cid]
        assert len(son_data) == 1, f"Son not found in mother's children: {data}"
        assert son_data[0]['source'] == 'via_spouse'
    
    def test_child_gets_mother_via_father_marriage(self, logged_in_client):
        """Child queries parents → should get both father (direct) and mother (inferred)."""
        gid, fid, mid, cid = self._create_family(logged_in_client)
        if not cid:
            pytest.skip("Setup failed")
        
        resp = logged_in_client.get(f'/api/members/{cid}/parents')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2, f"Expected >=2 parents, got {data}"
        
        father_data = [d for d in data if d['member_id'] == fid and d['source'] == 'direct']
        mother_data = [d for d in data if d['member_id'] == mid and d['source'] == 'inferred']
        assert len(father_data) == 1, "Father (direct) missing"
        assert len(mother_data) == 1, "Mother (inferred) missing"
        assert mother_data[0]['relation_type'] == 'mother'
    
    def test_kinship_mother_to_son(self, logged_in_client):
        """Kinship between mother and son (via father marriage)."""
        gid, fid, mid, cid = self._create_family(logged_in_client)
        if not cid:
            pytest.skip("Setup failed")
        
        resp = logged_in_client.get(
            f'/api/relations/kinship?member_a={mid}&member_b={cid}'
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None, f"Kinship should exist between mother and son, got {data}"
        assert data.get('total_distance', -1) >= 2, "Path via father should have distance >= 2"
    
    def test_kinship_spouse_to_spouse(self, logged_in_client):
        """Kinship between husband and wife (direct marriage)."""
        gid, fid, mid, cid = self._create_family(logged_in_client)
        if not cid:
            pytest.skip("Setup failed")
        
        resp = logged_in_client.get(
            f'/api/relations/kinship?member_a={fid}&member_b={mid}'
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None, f"Kinship should exist between spouses, got {data}"
        assert data.get('total_distance', -1) >= 1
    
    def _create_extended_family(self, client):
        """
        Helper: create 3-generation family.
        Grandfather(M) ←→ Grandmother(F) [married]
        └── Father(M) ←→ Mother(F) [married]
            └── Son(M) + Daughter(F)
        Only father→child links exist; mother/grandmother linked only via marriage.
        Returns 7 values: gid, gfid, gmid, fid, mid, sid, did
        """
        gid_resp = client.post('/api/genealogies', json={
            'name': f'Multigen Test {uuid.uuid4().hex[:6]}',
            'surname': 'MultiGen'
        })
        if gid_resp.status_code != 201:
            return [None] * 7
        gid = gid_resp.get_json()['genealogy_id']

        ids = {}
        for role, gender, year in [
            ('grandfather', 'M', 1930), ('grandmother', 'F', 1932),
            ('father', 'M', 1960), ('mother', 'F', 1962),
            ('son', 'M', 1990), ('daughter', 'F', 1992)
        ]:
            resp = client.post(f'/api/genealogies/{gid}/members', json={
                'name': role.capitalize(), 'gender': gender, 'birth_year': year
            })
            if resp.status_code != 201:
                return [None] * 7
            ids[role] = resp.get_json()['member_id']

        for a, b in [('grandfather', 'grandmother'), ('father', 'mother')]:
            mr = client.post('/api/relations/marriage', json={
                'member_id1': ids[a], 'member_id2': ids[b],
                'marriage_year': 1955 if 'grand' in a else 1985
            })
            if mr.status_code not in (200, 201):
                return [None] * 7

        for child, parent in [('father', 'grandfather'), ('son', 'father'), ('daughter', 'father')]:
            lr = client.post('/api/relations/link', json={
                'child_id': ids[child], 'parent_id': ids[parent], 'relation_type': 'father'
            })
            if lr.status_code not in (200, 201):
                return [None] * 7

        return gid, ids['grandfather'], ids['grandmother'], ids['father'], ids['mother'], ids['son'], ids['daughter']

    def test_mother_ancestors_include_inlaws(self, logged_in_client):
        """Mother queries ancestors → should see husband's father/grandfather via marriage."""
        result = self._create_extended_family(logged_in_client)
        if not result[0]:
            pytest.skip("Setup failed")
        gid, gfid, gmid, fid, mid, sid, did = result

        resp = logged_in_client.get(f'/api/members/{mid}/ancestors')
        assert resp.status_code == 200
        data = resp.get_json()
        ancestor_ids = {a['member_id'] for a in data}
        # Mother should see father-in-law (grandfather) and father (via marriage)
        assert fid in ancestor_ids, f"Father should be in mother's ancestors: {data}"
        assert gfid in ancestor_ids, f"Grandfather should be in mother's ancestors: {data}"

    def test_grandfather_descendants_include_daughter_in_law(self, logged_in_client):
        """Grandfather queries descendants → should see daughter-in-law (mother) via marriage."""
        result = self._create_extended_family(logged_in_client)
        if not result[0]:
            pytest.skip("Setup failed")
        gid, gfid, gmid, fid, mid, sid, did = result

        resp = logged_in_client.get(f'/api/members/{gfid}/descendants')
        assert resp.status_code == 200
        data = resp.get_json()
        descendant_ids = {d['member_id'] for d in data}
        assert fid in descendant_ids, f"Father should be in descendants: {data}"
        assert mid in descendant_ids, f"Mother should be in descendants via marriage: {data}"
        assert sid in descendant_ids, f"Son should be in descendants: {data}"

    def test_son_ancestors_include_both_sides(self, logged_in_client):
        """Son queries ancestors → should see both father's and mother's sides."""
        result = self._create_extended_family(logged_in_client)
        if not result[0]:
            pytest.skip("Setup failed")
        gid, gfid, gmid, fid, mid, sid, did = result

        resp = logged_in_client.get(f'/api/members/{sid}/ancestors')
        assert resp.status_code == 200
        data = resp.get_json()
        ancestor_ids = {a['member_id'] for a in data}
        assert fid in ancestor_ids, "Father missing"
        assert mid in ancestor_ids, "Mother (inferred via marriage) missing"
        assert gfid in ancestor_ids, "Grandfather missing"
        # Grandmother should also be reachable (via grandfather's marriage)
        assert gmid in ancestor_ids, "Grandmother (inferred) missing"

    def test_father_gets_child_direct(self, logged_in_client):
        """Father queries children → should get son directly."""
        gid, fid, mid, cid = self._create_family(logged_in_client)
        if not cid:
            pytest.skip("Setup failed")
        
        resp = logged_in_client.get(f'/api/members/{fid}/children')
        assert resp.status_code == 200
        data = resp.get_json()
        son_data = [d for d in data if d['member_id'] == cid]
        assert len(son_data) == 1, f"Father should find son directly: {data}"
        assert son_data[0]['source'] == 'direct'


class TestQueryKinship:
    """Test query kinship between two members."""
    
    def test_query_kinship_success(self, logged_in_client):
        """Test querying kinship path."""
        gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
        if pid and cid:
            # Establish relationship first
            link_resp = logged_in_client.post('/api/relations/link', json={
                'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
            })
            assert link_resp.status_code in [200, 201]
            resp = logged_in_client.get(
                f'/api/relations/kinship?member_a={pid}&member_b={cid}'
            )
            assert resp.status_code == 200
    
    def test_query_kinship_missing_params(self, logged_in_client):
        """Test kinship query with missing parameters."""
        resp = logged_in_client.get('/api/relations/kinship')
        assert resp.status_code == 400
    
    def test_query_kinship_requires_login(self, client):
        """Test kinship query without login."""
        resp = client.get('/api/relations/kinship?member_a=1&member_b=2')
        assert resp.status_code == 401