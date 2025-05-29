# rosbuddy/file_generators/package_xml_generator.py
import textwrap
from rosbuddy.data_models.package_config import PackageConfig, Dependency, Export
from typing import List, Dict, Any, Optional # Ensure typing imports are present

# --- Helper functions that were mistakenly omitted in the previous version ---
def _generate_maintainers_xml(maintainers: list) -> str:
    xml_parts = []
    for maint in maintainers:
        xml_parts.append(f'  <maintainer email="{maint["email"]}">{maint["name"]}</maintainer>')
    return "\n".join(xml_parts)

def _generate_licenses_xml(licenses: list) -> str:
    xml_parts = []
    for lic in licenses:
        xml_parts.append(f'  <license>{lic}</license>')
    return "\n".join(xml_parts)

def _generate_authors_xml(authors: list) -> str:
    xml_parts = []
    for author in authors:
        email_attr = f' email="{author["email"]}"' if "email" in author and author["email"] else ""
        xml_parts.append(f'  <author{email_attr}>{author["name"]}</author>')
    return "\n".join(xml_parts)

def _generate_urls_xml(urls: list) -> str:
    xml_parts = []
    for url_info in urls:
        type_attr = f' type="{url_info["type"]}"' if "type" in url_info and url_info["type"] else ""
        xml_parts.append(f'  <url{type_attr}>{url_info["url"]}</url>')
    return "\n".join(xml_parts)
# --- End of re-added helper functions ---


def _generate_dependencies_xml(dependencies: list[Dependency], has_interfaces: bool, build_type: str) -> list[str]:
    managed_deps: Dict[tuple[str, str], str] = {}

    def add_or_update_dep(name: str, dep_type: str, version_attrs_str: str = ""):
        key = (name, dep_type)
        managed_deps[key] = f'  <{dep_type}{version_attrs_str}>{name}</{dep_type}>'

    if build_type == "ament_cmake":
        add_or_update_dep("ament_cmake", "buildtool_depend")
    elif build_type == "ament_python":
        add_or_update_dep("ament_python", "buildtool_depend")

    if has_interfaces:
        add_or_update_dep("rosidl_default_generators", "buildtool_depend")
        add_or_update_dep("rosidl_default_runtime", "exec_depend")

    for dep in dependencies:
        attrs = []
        if dep.version_lt: attrs.append(f'version_lt="{dep.version_lt}"')
        if dep.version_lte: attrs.append(f'version_lte="{dep.version_lte}"')
        if dep.version_eq: attrs.append(f'version_eq="{dep.version_eq}"')
        if dep.version_gte: attrs.append(f'version_gte="{dep.version_gte}"')
        if dep.version_gt: attrs.append(f'version_gt="{dep.version_gt}"')
        attr_str = (" " + " ".join(attrs)) if attrs else ""
        managed_deps[(dep.name, dep.dep_type)] = f'  <{dep.dep_type}{attr_str}>{dep.name}</{dep.dep_type}>'
        
    return sorted(list(managed_deps.values()))


def _generate_exports_xml(exports: list[Export], has_interfaces: bool, build_type: str) -> str:
    managed_exports: Dict[Any, str] = {}

    def add_or_update_export(tag_name: str, content: Optional[str] = None, attributes: Optional[Dict[str,str]] = None, unique_key: Optional[Any] = None):
        key = unique_key if unique_key is not None else tag_name
        
        attr_str_parts = []
        if attributes:
            for k, v in attributes.items():
                attr_str_parts.append(f'{k}="{v}"')
        attr_str = (" " + " ".join(attr_str_parts)) if attr_str_parts else ""

        if content is not None:
            managed_exports[key] = f'  <{tag_name}{attr_str}>{content}</{tag_name}>'
        else:
            managed_exports[key] = f'  <{tag_name}{attr_str}/>'

    if build_type:
        add_or_update_export("build_type", content=build_type)

    if has_interfaces:
        add_or_update_export("member_of_group", content="rosidl_interface_packages", unique_key=("member_of_group", "rosidl_interface_packages"))

    for exp in exports:
        unique_key_user = exp.tag_name
        # Special handling for unique keys if user defines build_type or specific member_of_group
        if exp.tag_name == "build_type":
             unique_key_user = "build_type" # Ensure user's build_type overrides auto one
        elif exp.tag_name == "member_of_group" and exp.content == "rosidl_interface_packages":
            unique_key_user = ("member_of_group", "rosidl_interface_packages")
        
        add_or_update_export(exp.tag_name, exp.content, exp.attributes, unique_key=unique_key_user)
        
    if not managed_exports:
        return ""
        
    return "<export>\n" + "\n".join(sorted(list(managed_exports.values()))) + "\n  </export>"


def generate_package_xml_content(config: PackageConfig) -> str:
    """Generates the complete XML content for a package.xml file."""
    has_interfaces = bool(getattr(config, 'interface_definitions', []))

    # Aggregate all unique dependencies from interface_package_dependencies
    interface_deps = set()
    if has_interfaces:
        for iface in config.interface_definitions:
            for dep in getattr(iface, 'interface_package_dependencies', []):
                if dep:
                    interface_deps.add(dep)
    # Convert to Dependency objects if not already present in config.dependencies
    all_deps = list(config.dependencies)
    dep_names = {d.name for d in all_deps}
    for dep_name in sorted(interface_deps):
        if dep_name not in dep_names:
            # Add as a generic <depend> (could be improved to be more specific if needed)
            all_deps.append(Dependency(name=dep_name, dep_type="depend"))

    maintainers_xml = _generate_maintainers_xml(config.maintainers)
    licenses_xml = _generate_licenses_xml(config.licenses)
    authors_xml = _generate_authors_xml(config.authors) if config.authors else ""
    urls_xml = _generate_urls_xml(config.urls) if config.urls else ""
    
    dependencies_xml_list = _generate_dependencies_xml(all_deps, has_interfaces, config.build_type)
    exports_section_xml = _generate_exports_xml(config.exports, has_interfaces, config.build_type)

    test_depends_xml = textwrap.dedent("""\
      <test_depend>ament_copyright</test_depend>
      <test_depend>ament_flake8</test_depend>
      <test_depend>ament_pep257</test_depend>
      <test_depend>python3-pytest</test_depend>""")

    xml_lines = [
        '<?xml version="1.0"?>',
        '<package format="3">',
        f'  <name>{config.name}</name>',
        f'  <version>{config.version}</version>',
        f'  <description>{config.description}</description>',
        maintainers_xml, # This line will now work
        licenses_xml,
    ]
    if authors_xml: xml_lines.append(authors_xml)
    if urls_xml: xml_lines.append(urls_xml)
    
    # Add a blank line before dependencies if there were authors or urls
    if authors_xml or urls_xml:
        xml_lines.append("")
    xml_lines.extend(dependencies_xml_list) 
    
    if exports_section_xml:
         xml_lines.append("") # Blank line before exports
         xml_lines.append(exports_section_xml)
    
    xml_lines.append("") # Blank line before test_depends
    xml_lines.append(test_depends_xml)
    xml_lines.append('</package>')

    # Join and filter out any completely blank lines that might result from empty sections
    # but preserve single newlines from join.
    final_xml_string = "\n".join(xml_lines)
    # Clean up multiple consecutive blank lines that might arise if sections are empty
    while "\n\n\n" in final_xml_string:
        final_xml_string = final_xml_string.replace("\n\n\n", "\n\n")
        
    return final_xml_string