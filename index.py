import datetime
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from app import app
from apps.models import login
from apps.views.app3 import capacity_div
from flask_login import logout_user, current_user
from apps.views import app1, app2, app3, user_admin, error

current_time = html.Div(
    html.Div([
        html.Div(id='live-update-time'),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        )
    ])
)

navBar = dbc.Navbar(id='navBar',
                    children=[],
                    sticky='top',
                    color='primary',
                    className='navbar navbar-expand-lg navbar-dark bg-primary',
                    style={'height': '55px', 'margin-bottom': '5px'}
                    )

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        navBar,
        html.Div(id='page-content'),
    ])
], id='table-wrapper')


#########################################################
# HANDLE PAGE ROUTING - IF USER NOT LOGGED IN, ALWAYS RETURN TO LOGIN SCREEN
################################################################################
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def displayPage(pathname):
    if pathname == '/':
        if current_user.is_authenticated:
            return app1.layout
        else:
            return login.layout

    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return login.layout
        else:
            return login.layout

    if pathname == '/apps/app1':
        if current_user.is_authenticated:
            return app1.layout
        else:
            return login.layout

    if pathname == '/apps/app2':
        if current_user.is_authenticated:
            return app2.layout
        else:
            return login.layout

    if pathname == '/apps/app3':
        if current_user.is_authenticated:
            return app3.layout
        else:
            return login.layout

    if pathname == '/profile':
        if current_user.is_authenticated:
            return app1.layout
        else:
            return login.layout

    if pathname == '/admin':
        if current_user.is_authenticated:
            if current_user.admin == 1:
                return user_admin.layout
            else:
                return error.layout
        else:
            return login.layout

    else:
        return error.layout


#####################################################
# ONLY SHOW NAVIGATION BAR WHEN A USER IS LOGGED IN
#####################################################
@app.callback(
    Output('navBar', 'children'),
    [Input('page-content', 'children')])
def navBar(input1):
    if current_user.is_authenticated:
        if current_user.admin == 1:
            navBarContents = [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="../assets/qub2.jpg", height="35px")),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="https://www.qub.ac.uk/",
                ),
                dbc.NavbarBrand("Dashboard", href="/apps/app3", className="nav-link"),
                dbc.NavbarBrand("Search", href="/apps/app2", className="nav-link"),
                # dbc.NavbarBrand("Homepage", href="/apps/app1", className="nav-link"),
                dbc.Nav([capacity_div], className="align-self-center, ml-auto"),
                dbc.Nav([current_time], className="ml-auto"),
                dbc.DropdownMenu(
                    nav=True,
                    in_navbar=True,
                    label=current_user.username,
                    style={'text-transform': 'capitalize'},
                    children=[
                        dbc.DropdownMenuItem('Admin', href='/admin'),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem('Logout', href='/logout'),
                    ],
                    className="nav-link dropdown-toggle"
                ),
            ]
            return navBarContents

        else:
            navBarContents = [

                dbc.NavbarBrand("Dashboard", href="/apps/app3", className="nav-link"),
                dbc.NavbarBrand("Homepage", href="/apps/app1"),
                dbc.NavbarBrand("Search", href="/apps/app2"),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.DropdownMenu(
                        nav=True,
                        in_navbar=True,
                        label=current_user.username.capitilize(),
                        children=[
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem('Logout', href='/logout'),
                        ],
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ]
            return navBarContents
    else:
        return ''

# gives and displays current time
@app.callback(Output('live-update-time', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_time(n):
    time = str(datetime.datetime.now().strftime("%H:%M:%S"))
    return [
        html.H4(time,
                className="text-light",
                style={'color': '#00000'},
                ),
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
