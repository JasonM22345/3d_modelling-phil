# app.py
import streamlit as st
from stmol import showmol
import py3Dmol
from helper_functions import (
    read_xyz,
    write_xyz,
    replace_atom_with_group,
    add_group_to_atom,
    delete_atoms,
    create_xyz_string,
)

st.title("Structural Modification of Molecules")

uploaded_file = st.file_uploader("Upload XYZ File", type="xyz")

if uploaded_file is not None:
    # Parse XYZ input
    try:
        atomic_symbols, atomic_coordinates = read_xyz(uploaded_file)
    except Exception as e:
        st.error(f"Error processing XYZ file: {e}")
        st.stop()

    st.subheader("Original Molecule Structure")
    xyz_string = create_xyz_string(atomic_symbols, atomic_coordinates)

    view = py3Dmol.view(width=800, height=400)
    view.addModel(xyz_string, "xyz")
    view.setStyle({'sphere': {'radius': 0.3}, 'stick': {'radius': 0.15}})
    for i, (symbol, coords) in enumerate(zip(atomic_symbols, atomic_coordinates)):
        view.addLabel(
            f"{i+1}",
            {
                "position": {"x": coords[0], "y": coords[1], "z": coords[2]},
                "fontSize": 14,
                "fontColor": "black",
                "backgroundOpacity": 0.2,
            },
        )
    view.zoomTo()
    showmol(view, height=400, width=800)

    # Sidebar for modification controls
    st.sidebar.header("Modification Controls")

    # Expanded list of functional groups
    groups = {
        "Alkyl Groups": {
            "Methyl (-CH3)": ["C", "H", "H", "H"],
            "Ethyl (-CH2CH3)": ["C", "H", "H", "C", "H", "H", "H"],
            "Propyl (-CH2CH2CH3)": ["C", "H", "H", "C", "H", "H", "C", "H", "H", "H"],
        },
        "Oxygen-containing Groups": {
            "Hydroxyl (-OH)": ["O", "H"],
            "Carbonyl (=O)": ["O"],
            "Carboxyl (-COOH)": ["C", "O", "O", "H"],
            "Ether (-OR)": ["O", "C", "H", "H", "H"],
            "Ester (-COOR)": ["C", "O", "O", "C", "H", "H", "H"],
        },
        "Nitrogen-containing Groups": {
            "Amino (-NH2)": ["N", "H", "H"],
            "Amide (-CONH2)": ["C", "O", "N", "H", "H"],
            "Nitro (-NO2)": ["N", "O", "O"],
        },
        "Halogen Groups": {
            "Fluoro (-F)": ["F"],
            "Chloro (-Cl)": ["Cl"],
            "Bromo (-Br)": ["Br"],
            "Iodo (-I)": ["I"],
        },
        "Sulfur-containing Groups": {
            "Thiol (-SH)": ["S", "H"],
            "Sulfone (-SO2-)": ["S", "O", "O"],
        },
        "Phosphorus-containing Groups": {
            "Phosphate (-PO4)": ["P", "O", "O", "O", "O"],
        },
    }

    modifications = []
    count = 0
    while True:
        st.sidebar.subheader(f"Modification {count + 1}")

        mod_type = st.sidebar.radio(
            "Modification type:",
            ["Substitution", "Addition", "Deletion"],
            key=f"mod_type_{count}",
        )

        atom_choices = list(range(1, len(atomic_symbols) + 1))
        selected_atoms = st.sidebar.multiselect(
            "Select atom(s) to modify:",
            options=atom_choices,
            format_func=lambda x: f"{atomic_symbols[x-1]} at position {x}",
            key=f"atoms_{count}",
        )

        if mod_type in ["Substitution", "Addition"]:
            category = st.sidebar.selectbox(
                "Group category:", list(groups.keys()), key=f"cat_{count}"
            )
            group_name = st.sidebar.selectbox(
                "Functional group:", list(groups[category].keys()), key=f"group_{count}"
            )
            group = groups[category][group_name]
        else:
            group = None

        for atom_index in selected_atoms:
            modifications.append((mod_type, atom_index - 1, group))

        if not st.sidebar.checkbox("Add another modification", key=f"next_{count}"):
            break
        count += 1

    if st.sidebar.button("Perform Modifications"):
        new_symbols = atomic_symbols.copy()
        new_coords = atomic_coordinates.copy()

        # Deletions must be last to avoid index shifting
        modifications.sort(key=lambda x: x[0] == "Deletion")

        for mod_type, idx, group in modifications:
            if mod_type == "Substitution":
                new_symbols, new_coords = replace_atom_with_group(
                    new_symbols, new_coords, idx, group
                )
            elif mod_type == "Addition":
                new_symbols, new_coords = add_group_to_atom(
                    new_symbols, new_coords, idx, group
                )
            elif mod_type == "Deletion":
                new_symbols, new_coords = delete_atoms(new_symbols, new_coords, [idx])

        # Show updated structure
        st.subheader("Modified Molecule Structure")
        new_xyz = create_xyz_string(new_symbols, new_coords)

        view = py3Dmol.view(width=800, height=400)
        view.addModel(new_xyz, "xyz")
        view.setStyle({'sphere': {'radius': 0.3}, 'stick': {'radius': 0.15}})
        for i, (symbol, coords) in enumerate(zip(new_symbols, new_coords)):
            view.addLabel(
                f"{i+1}",
                {
                    "position": {"x": coords[0], "y": coords[1], "z": coords[2]},
                    "fontSize": 14,
                    "fontColor": "black",
                    "backgroundOpacity": 0.2,
                },
            )
        view.zoomTo()
        showmol(view, height=400, width=800)

        st.download_button(
            label="Download Modified XYZ File",
            data=write_xyz(new_symbols, new_coords),
            file_name="modified_molecule.xyz",
            mime="text/plain",
        )
