from services.config import AppConfig

class Loader:
    def __init__(self, config: AppConfig, friends: list):
        self.config = config
        self.friends = friends


    def load_friends(self)->str:
        """ coordinator, prepare data and generate markdown """
        if not self.friends or not isinstance(self.friends, list):
            return "### no friends"

        sorted_friends = self.sort_friends()
        return self.to_markdown(sorted_friends)


    def sort_friends(self)->list:
        """ determine the output list order """
        def get_key(friend):
            main = friend.main
            role = None
            if main.specs:
                preferred_spec = list(main.specs.values())[0]
                role = preferred_spec.get("role")
            # sort by sightings -> role -> class/type
            return (friend.sightings, role or main.type)

        return sorted(self.friends, key=get_key, reverse=True)


    def specs_to_markdown(self, alt) -> str:
        """ properly format a markdown string based on spec info """
        # alt specs markdown
        if len(alt.specs) > 1:
            specs = [f"{info["sightings"]} {name}" for name, info in alt.specs.items()]
            spec_md = " - ".join(specs)
        elif len(alt.specs) == 1:
            spec_md = next(iter(alt.specs))
        else:
            spec_md = ""
        spec_md += " | " if spec_md else ""
        return spec_md


    def to_markdown(self, friends: list) -> str:
        """ create a markdown list of friends """
        guild = self.config.guild_name
        raid = self.config.raid

        header_md = []
        if guild:
            header_md.append(f"# {guild}")
        header_md.append(f"## Midnight - Season 1")
        if raid and "name" in raid:
            header_md.append(f"{raid["name"]}")
        header_md.append("AotC prog roster")
        header_md.append("**Friends** | pulls\n")

        threshold = 20
        raider_list = [f for f in friends if f.sightings > threshold]
        assist_list = [f for f in friends if f.sightings <= threshold]

        core_md = []
        for raider in raider_list:
            # main name | total pulls
            raider_md = [f"**{raider.main.name}** | {raider.sightings}"]
            for alt in raider.alts:
                spec_md = self.specs_to_markdown(alt)
                raider_md.append(f"  {alt.sightings} | {alt.name}-{alt.server} | {spec_md}{alt.type}")
            core_md.append("\n".join(raider_md))

        assist_md = []
        for friend in assist_list:
            for alt in friend.alts:
                spec_md = self.specs_to_markdown(alt)
                assist_md.append(f"{alt.sightings} | {alt.name}-{alt.server} | {spec_md}{alt.type}")

        final_md = [
            "\n".join(header_md),
            "\n".join(core_md),
            "",
            "\n".join(assist_md) ]

        return "\n".join(md for md in final_md)

