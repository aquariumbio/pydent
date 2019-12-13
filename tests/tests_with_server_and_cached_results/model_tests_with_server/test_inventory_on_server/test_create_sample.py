import time
from uuid import uuid4

# pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
#                               "In the future, we may want to utilize something like pyvrc to avoid"
#                               "sending live requests to Aquarium.")


def test_create_sample(session):

    st = session.SampleType.find_by_name("Yeast Strain")

    new_yeast = session.Sample.new(
        name="mynewsample" + str(uuid4()), project="trident", sample_type_id=st.id
    )

    def empty_prop_dict(sample_type):
        return {ft.name: None for ft in sample_type.field_types}

    def init_props(prop_dict, sample_type):
        fts = sample_type.field_types
        ft_names = [ft.name for ft in fts]
        ft_dict = dict(zip(ft_names, fts))
        fvs = []
        for prop, val in prop_dict.items():
            if val is not None:
                ft = ft_dict[prop]
                afts = ft.allowable_field_types
                fv = ft.initialize_field_value()

                if afts is None or afts == []:
                    fv.set_value(value=val)
                else:
                    fv.set_value(sample=val)
                fvs.append(fv)
        return fvs

    prop = empty_prop_dict(st)

    plasmid = session.Sample.find(9246)
    prop["Comp_cell_limit"] = "No"
    prop["Integrant"] = plasmid
    fvs = init_props(prop, st)

    new_yeast.field_values = fvs

    new_yeast.save()

    s = session.Sample.find(new_yeast.id)
    assert s.properties["Integrant"].id == plasmid.id


def test_init_sample_with_properties(session):

    new_yeast = session.Sample.new(
        name="mynewsample" + str(uuid4()),
        project="trident",
        sample_type_id=session.SampleType.find_by_name("Yeast Strain").id,
        properties={
            "Integrant": session.Sample.find_by_name("DummyPlasmid"),
            "QC_length": 1313,
        },
    )

    new_yeast.save()


def test_create_sample2(session):
    def yeast_integrant_name(yname, pname):
        return "|".join([yname.strip(), pname.strip()])[:100]

    def integrate_plasmid(yeast, plasmid):
        yeast_name = yeast_integrant_name(yeast.name, plasmid.name) + str(uuid4())

        new_yeast = yeast.session.Sample.new(
            name=yeast_name,
            project="trident",
            sample_type_id=yeast.sample_type_id,
            properties={
                "Mating Type": yeast.properties["Mating Type"],
                "Integrant": plasmid,
                "Has this strain passed QC?": "No",
                "Parent": yeast,
                "Integrated Marker(s)": "HIS",  # plasmid.properties["Yeast Marker"]
            },
        )
        new_yeast.save()
        return new_yeast

    yeast = session.Sample.one(
        query={"sample_type_id": session.SampleType.find_by_name("Yeast Strain").id}
    )
    plasmids = session.Sample.last(
        2, query={"sample_type_id": session.SampleType.find_by_name("Plasmid").id}
    )

    # test save and reload
    integrate_plasmid(yeast, plasmids[0])
    loaded = session.Sample.find(yeast.id)
    assert loaded.properties["Integrant"].id == plasmids[0].id

    # test update
    loaded.update_properties({"Integrant": plasmids[1]})
    loaded.save()
    assert loaded.properties["Integrant"].id == plasmids[1].id
    reloaded = session.Sample.find(loaded.id)
    assert reloaded.properties["Integrant"].id == plasmids[1].id
