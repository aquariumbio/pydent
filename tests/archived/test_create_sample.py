from uuid import uuid4
import pytest

pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
                              "In the future, we may want to utilize something like pyvrc to avoid"
                              "sending live requests to Aquarium.")


def test_create_sample(session):

    st = session.SampleType.find_by_name("Yeast Strain")

    new_yeast = session.Sample.new(
        name="mynewsample" + str(uuid4()),
        project="trident",
        sample_type_id=st.id,
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
    print(new_yeast.dump(include={"field_values": {"sid"}}))

    new_yeast.save()

    s = session.Sample.find(new_yeast.id)
    assert s.properties["Integrant"].id == plasmid.id


def test_init_sample_with_properties(session):


    new_yeast = session.Sample.new(
        name="mynewsample" + str(uuid4()),
        project="trident",
        sample_type_id=session.SampleType.find_by_name("Yeast Strain").id,
        properties={
            "Integrant": session.Sample.find_by_name("DummyPlasmid")
        }
    )

    new_yeast.save()